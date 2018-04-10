# toy example of the full pipeline
from datasets import fetch_two_voice_species1
from analysis import notes_to_midi
import numpy as np


def two_voice_species1_wrap():
    all_ex = fetch_two_voice_species1()
    # for now, just get info from 2 voice species 1
    #all_ex += fetch_three_voice_species1()
    all_index = []
    all_tb = []
    all_lower_midi = []
    all_upper_midi = []
    all_lower_offset = []
    all_upper_offset = []
    for ii, ex in enumerate(all_ex):
        # skip any "wrong" examples
        if not all(ex["answers"]):
            continue
        all_index.append(ex["name"])
        nd = ex["notes_and_durations"]
        notes = [[ndii[0] for ndii in ndi] for ndi in nd]
        # durations not used in first species, leave it alone
        durations = [[ndii[1] for ndii in ndi] for ndi in nd]
        midi = notes_to_midi(notes)
        cf = ex["cantus_firmus_voice"]

        all_lower_offset.append([99] + list(np.array(midi[1]) - midi[1][-1]) + [100])
        all_upper_offset.append(list(np.array(midi[0]) - midi[0][-1]))

        all_upper_midi.append(midi[0])
        all_lower_midi.append(midi[1])

        tb = [97] + list(np.array(midi[0]) - np.array(midi[1]))
        all_tb.append(tb)

    flat_tb = [ddd for dd in all_tb for ddd in dd]
    # these are the actions
    # they map to intervals wrt bottom voice
    # [-8, -4, -3, 0, 3, 4, 7, 8, 9, 12, 15, 16, 97]
    # 97 reserved for start of sequence
    tb_set = sorted(list(set(flat_tb)))
    tb_map = {v: k for k, v in enumerate(tb_set)}
    tb_rev_map = {v: k for k, v in tb_map.items()}

    flat_lower_offset = [ddd for dd in all_lower_offset for ddd in dd]
    # these are input symbols from bottom_voice, as offsets relative to last note ("key" centered)
    # [-12, -10, -9, -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 99, 100]
    # 99 reserved for start of lower indicator
    # 100 reserved for end of lower indicator
    lower_offset_set = sorted(list(set(flat_lower_offset)))
    lower_map = {v: k for k, v in enumerate(lower_offset_set)}
    lower_rev_map = {v: k for k, v in lower_map.items()}

    def make_windows(all_tb, all_lower_offset, lower_window=3, upper_lookback=1):
        # not general
        assert upper_lookback < lower_window
        all_instances = []
        for ii in range(len(all_tb)):
            tb = all_tb[ii]
            lower_offset = all_lower_offset[ii]
            instances = []
            for kk in range(upper_lookback, len(lower_offset) - lower_window + lower_window // 2 + 1):
                lookback = tb[kk - upper_lookback:kk]
                window = lower_offset[kk - upper_lookback:kk + lower_window - upper_lookback]
                instances.append([lookback, window])
            all_instances += instances
        return all_instances

    list_data = make_windows(all_tb, all_lower_offset)
    data_p = np.array([[tb_map[ldi] for ldi in ld[0]] for ld in list_data])
    data_l = np.array([[lower_map[ldi] for ldi in ld[1]] for ld in list_data])
    return data_p, data_l, tb_map, lower_map, all_tb, all_lower_offset, all_index

if __name__ == "__main__":
    two_voice_species1_wrap()
