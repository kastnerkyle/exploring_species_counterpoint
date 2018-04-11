from dataset_wrap import two_voice_species1_wrap
from analysis import analyze_two_voices
import numpy as np

window_p, window_l, p_map, l_map, all_p, all_l, all_i = two_voice_species1_wrap()

l_inv_map = {v: k for k, v in l_map.items()}
p_inv_map = {v: k for k, v in p_map.items()}

class MusicStateManager(object):
    def __init__(self, default_mode="C", random_state=None):
        if random_state is None:
            raise ValueError("Must pass random_state")
        self.random_state = random_state
        self.default_mode = default_mode
        # map guide trace values
        self.guide_map = l_map
        self.guide_inv_map = l_inv_map
        # map of original
        self.original_map = p_map
        self.original_inv_map = p_inv_map
        # don't allow unison
        self.valid_action_map = {k: p_map[k] for k in sorted(p_map.keys()) if k < 97 and k != 0}
        # real movement to policy
        # policy action to real movement
        self.valid_action_inv_map = {v: k for k, v in self.valid_action_map.items()}
        self.valid_action_size = len(self.valid_action_map.keys())

        self.valid_action_remapper = {k: v for k, v in enumerate(sorted(self.valid_action_inv_map.keys()))}
        self.valid_action_inv_remapper = {v: k for k, v in self.valid_action_remapper.items()}

        # C3
        self.offset_value = 48
        self.current_ind_ = self.random_state.randint(len(all_l))
        self.current_guide_ = all_l[self.current_ind_]

        self.step_ = 0
        # 97 is default step state
        self.last_action_ = p_map[97]
        self.init_state_ = self.state_maker(self.step_)

    def state_maker(self, i):
        if i > (len(self.current_guide_) - 3):
            raise ValueError("i > guide")
        p = [self.last_action_]
        l = [l_map[g] for g in self.current_guide_[i:i + 3]]
        state = np.array(p + l)
        return state

    def next_state(self, state, action):
        self.last_action_ = action
        self.step_ += 1
        next_state = self.state_maker(self.step_)
        return next_state

    def reset(self, partial=False):
        if partial == False:
            self.current_ind_ = self.random_state.randint(len(all_l))
            self.current_guide_ = all_l[self.current_ind_]
        self.step_ = 0
        # 97 is default step state
        self.last_action_ = p_map[97]
        self.init_state_ = self.state_maker(self.step_)

    def valid_actions(self, state):
        # don't choose invalid actions...
        return tuple(range(self.valid_action_size))

    def finished(self, state):
        if state[-1] == l_map[100]:
            return 1, True
        else:
            return 0, False

    def reconstruct_sequence(self, state_trace):
        np_st = np.array(state_trace)
        upper = list(np_st[:, 0])
        lower = [state_trace[0][2]]
        for ii in range(len(state_trace)):
            lower += [np_st[ii, -1]]
        lower_midi_orig = [l_inv_map[li] for li in lower]
        # double remap is to avoid pruned out actions and still get the right result
        pp_map = {}
        for k, v in self.valid_action_remapper.items():
            pp_map[k] = self.valid_action_inv_map[v]
        # add back the invalid action to handle first step decoding
        pp_map[p_map[97]] = 97
        self.pp_map = pp_map
        upper_interval_orig = [pp_map[pi] for pi in upper]
        # 97 is the boundary for special start, end of sequence stuff
        lower_midi = [lm for lm in lower_midi_orig if lm < 97]
        lower_midi = np.array(lower_midi) + self.offset_value
        upper_interval = [ui for ui in upper_interval_orig if ui < 97]
        # edge case at the end of partial sequences during playout
        upper_midi = np.array(upper_interval)[:len(lower_midi)] + lower_midi
        if len(lower_midi) < len(upper_interval):
            assert all([li > 97 for li in lower_midi_orig[len(lower_midi):]])
        midi = [[um for um in upper_midi], [lm for lm in lower_midi]]
        return midi

    def evaluate_sequence(self, midi_sequence, minimal=False):
        parts = midi_sequence
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        # minimal check is during rollout/playout, avoid checking start / end of sequence rules among others
        if minimal:
            aok = analyze_two_voices(parts, durations, key_signature, time_signature,
                                     species="species1_minimal", cantus_firmus_voices=[1])
        else:
            aok = analyze_two_voices(parts, durations, key_signature, time_signature,
                                     species="species1", cantus_firmus_voices=[1])
        return aok
