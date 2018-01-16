# Author: Kyle Kastner
# License: BSD 3-Clause
from music21 import converter
import numpy as np
import os

def music21_to_pitch_duration(p):
    """
    Taken from pthbldr

    Takes in a Music21 score, and outputs 3 list of list
    One for pitch
    One for duration
    list for part times of each voice
    """
    parts = []
    parts_times = []
    parts_delta_times = []
    for i, pi in enumerate(p.parts):
        part = []
        part_time = []
        part_delta_time = []
        total_time = 0
        for n in pi.stream().flat.notesAndRests:
            if n.isRest:
                part.append(0)
            else:
                try:
                    part.append(n.midi)
                except AttributeError:
                    continue
            part_time.append(total_time + n.duration.quarterLength)
            total_time = part_time[-1]
            part_delta_time.append(n.duration.quarterLength)
        parts.append(part)
        parts_times.append(part_time)
        parts_delta_times.append(part_delta_time)
    return parts, parts_times, parts_delta_times

def pitch_and_duration_to_piano_roll(list_of_pitch_voices, list_of_duration_voices, min_dur):
    def expand(pitch, dur, min_dur):
        assert len(pitch) == len(dur)
        expanded = [int(d // min_dur) for d in dur]
        check = [d / min_dur for d in dur]
        assert all([e == c for e, c in zip(expanded, check)])
        stretch = [[p] * e for p, e in zip(pitch, expanded)]
        # flatten out to 1 voice
        return [pi for p in stretch for pi in p]

    res = []
    for lpv, ldv in zip(list_of_pitch_voices, list_of_duration_voices):
        qi = expand(lpv, ldv, min_dur)
        res.append(qi)

    min_len = min([len(ri) for ri in res])
    res = [ri[:min_len] for ri in res]
    piano_roll = np.array(res).transpose()
    return piano_roll


def pitches_and_durations_to_pretty_midi(pitches, durations,
                                         save_dir="samples",
                                         name_tag="sample_{}.mid",
                                         add_to_name=0,
                                         lower_pitch_limit=12,
                                         list_of_quarter_length=None,
                                         default_quarter_length=47,
                                         voice_params="woodwinds"):
    # allow list of list of list
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    durations assumed to be scaled to quarter lengths e.g. 1 is 1 quarter note
    2 is a half note, etc
    """
    is_seq_of_seq = False
    try:
        pitches[0][0]
        durations[0][0]
        if not hasattr(pitches, "flatten") and not hasattr(durations, "flatten"):
            is_seq_of_seq = True
    except:
        raise ValueError("pitches and durations must be a list of array, or list of list of list (time, voice, pitch/duration)")

    if is_seq_of_seq:
        if hasattr(pitches[0], "flatten"):
            # it's a list of array, convert to list of list of list
            pitches = [[[pitches[i][j, k] for j in range(pitches[i].shape[0])] for k in range(pitches[i].shape[1])] for i in range(len(pitches))]
            durations = [[[durations[i][j, k] for j in range(durations[i].shape[0])] for k in range(durations[i].shape[1])] for i in range(len(durations))]


    import pretty_midi
    # BTAS mapping
    def weird():
        voice_mappings = ["Sitar", "Orchestral Harp", "Acoustic Guitar (nylon)",
                          "Pan Flute"]
        voice_velocity = [20, 80, 80, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., .95]
        return voice_mappings, voice_velocity, voice_offset, voice_decay

    if voice_params == "weird":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
    elif voice_params == "weird_r":
        voice_mappings, voice_velocity, voice_offset, voice_decay = weird()
        voice_mappings = voice_mappings[::-1]
        voice_velocity = voice_velocity[::-1]
        voice_offset = voice_offset[::-1]
    elif voice_params == "nylon":
        voice_mappings = ["Acoustic Guitar (nylon)"] * 4
        voice_velocity = [20, 16, 25, 10]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., 1.]
        voice_decay = voice_decay[::-1]
    elif voice_params == "legend":
        # LoZ
        voice_mappings = ["Acoustic Guitar (nylon)"] * 3 + ["Pan Flute"]
        voice_velocity = [20, 16, 25, 5]
        voice_offset = [0, 0, 0, -12]
        voice_decay = [1., 1., 1., .95]
    elif voice_params == "organ":
        voice_mappings = ["Church Organ"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [.98, .98, .98, .98]
    elif voice_params == "piano":
        voice_mappings = ["Acoustic Grand Piano"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "electric_piano":
        voice_mappings = ["Electric Piano 1"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "harpsichord":
        voice_mappings = ["Harpsichord"] * 4
        voice_velocity = [40, 30, 30, 60]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    elif voice_params == "woodwinds":
        voice_mappings = ["Bassoon", "Clarinet", "English Horn", "Oboe"]
        voice_velocity = [50, 30, 30, 40]
        voice_offset = [0, 0, 0, 0]
        voice_decay = [1., 1., 1., 1.]
    else:
        # eventually add and define dictionary support here
        raise ValueError("Unknown voice mapping specified")

    # normalize
    mm = float(max(voice_velocity))
    mi = float(min(voice_velocity))
    dynamic_range = min(80, (mm - mi))
    # keep same scale just make it louder?
    voice_velocity = [int((80 - dynamic_range) + int(v - mi)) for v in voice_velocity]

    if not is_seq_of_seq:
        order = durations.shape[-1]
    else:
        try:
            # TODO: reorganize so list of array and list of list of list work
            order = durations[0].shape[-1]
        except:
            order = len(durations[0])
    voice_mappings = voice_mappings[-order:]
    voice_velocity = voice_velocity[-order:]
    voice_offset = voice_offset[-order:]
    voice_decay = voice_decay[-order:]
    if not is_seq_of_seq:
        pitches = [pitches[:, i, :] for i in range(pitches.shape[1])]
        durations = [durations[:, i, :] for i in range(durations.shape[1])]

    n_samples = len(durations)
    for ss in range(n_samples):
        durations_ss = durations[ss]
        pitches_ss = pitches[ss]
        # same number of voices
        assert len(durations_ss) == len(pitches_ss)
        # time length match
        assert all([len(durations_ss[i]) == len(pitches_ss[i]) for i in range(len(pitches_ss))])
        pm_obj = pretty_midi.PrettyMIDI()
        # Create an Instrument instance for a cello instrument
        def mkpm(name):
            return pretty_midi.instrument_name_to_program(name)

        def mki(p):
            return pretty_midi.Instrument(program=p)

        pm_programs = [mkpm(n) for n in voice_mappings]
        pm_instruments = [mki(p) for p in pm_programs]

        if list_of_quarter_length is None:
            # qpm to s per quarter = 60 s per min / quarters per min
            time_scale = 60. / default_quarter_length
        else:
            time_scale = 60. / list_of_quarter_length[ss]

        time_offset = np.zeros((order,))

        # swap so that SATB order becomes BTAS for voice matching
        pitches_ss = pitches_ss[::-1]
        durations_ss = durations_ss[::-1]

        # time
        for ii in range(len(durations_ss[0])):
            # voice
            for jj in range(order):
                try:
                    pitches_isj = pitches_ss[jj][ii]
                    durations_isj = durations_ss[jj][ii]
                except IndexError:
                    # voices may stop short
                    continue
                p = int(pitches_isj)
                d = durations_isj
                if d < 0:
                    continue
                if p < 0:
                    continue
                # hack out the whole last octave?
                s = time_scale * time_offset[jj]
                e = time_scale * (time_offset[jj] + voice_decay[jj] * d)
                time_offset[jj] += d
                if p < lower_pitch_limit:
                    continue
                note = pretty_midi.Note(velocity=voice_velocity[jj],
                                        pitch=p + voice_offset[jj],
                                        start=s, end=e)
                # Add it to our instrument
                pm_instruments[jj].notes.append(note)
        # Add the instrument to the PrettyMIDI object
        for pm_instrument in pm_instruments:
            pm_obj.instruments.append(pm_instrument)
        # Write out the MIDI data

        sv = save_dir + os.sep + name_tag.format(ss + add_to_name)
        try:
            pm_obj.write(sv)
        except ValueError:
            print("Unable to write file {} due to mido error".format(sv))


def quantized_to_pretty_midi(quantized,
                             quantized_bin_size,
                             save_dir="samples",
                             name_tag="sample_{}.mid",
                             add_to_name=0,
                             lower_pitch_limit=12,
                             list_of_quarter_length=None,
                             max_hold_bars=1,
                             default_quarter_length=47,
                             voice_params="woodwinds"):
    """
    takes in list of list of list, or list of array with axis 0 time, axis 1 voice_number (S,A,T,B)
    outer list is over samples, middle list is over voice, inner list is over time
    """

    is_seq_of_seq = False
    try:
        quantized[0][0]
        if not hasattr(quantized[0], "flatten"):
            is_seq_of_seq = True
    except:
        try:
            quantized[0].shape
        except AttributeError:
            raise ValueError("quantized must be a sequence of sequence (such as list of array, or list of list) or numpy array")

    # list of list or mb?
    n_samples = len(quantized)
    all_pitches = []
    all_durations = []

    max_hold = int(max_hold_bars / quantized_bin_size)
    if max_hold < max_hold_bars:
        max_hold = max_hold_bars

    for ss in range(n_samples):
        pitches = []
        durations = []
        if is_seq_of_seq:
            voices = len(quantized[ss])
            qq = quantized[ss]
        else:
            voices = quantized[ss].shape[1]
            qq = quantized[ss].T


        for i in range(voices):
            q = qq[i]
            pitch_i = [0]
            dur_i = []
            cur = 0
            count = 0
            for qi in q:
                if qi != cur:# or count > max_hold:
                    pitch_i.append(qi)
                    quarter_count = quantized_bin_size * (count + 1)
                    dur_i.append(quarter_count)
                    cur = qi
                    count = 0
                else:
                    count += 1
            quarter_count = quantized_bin_size * (count + 1)
            dur_i.append(quarter_count)
            pitches.append(pitch_i)
            durations.append(dur_i)
        all_pitches.append(pitches)
        all_durations.append(durations)
    pitches_and_durations_to_pretty_midi(all_pitches, all_durations,
                                         save_dir=save_dir,
                                         name_tag=name_tag,
                                         add_to_name=add_to_name,
                                         lower_pitch_limit=lower_pitch_limit,
                                         list_of_quarter_length=list_of_quarter_length,
                                         default_quarter_length=default_quarter_length,
                                         voice_params=voice_params)

def ribbons_from_piano_roll(piano_roll, ribbon_type, quantized_bin_size,
                            interval=12):
    from IPython import embed; embed(); raise ValueErro


def plot_piano_roll(piano_roll, quantized_bin_size,
                    pitch_bot=1, pitch_top=88,
                    colors=["red", "blue", "green", "purple"],
                    ribbons=False,
                    ribbon_type="std",
                    axis_handle=None,
                    autorange=True,
                    autoscale_ratio=0.25,
                    show=True,
                    show_rest_channel=False):
    # piano roll should be time x voices
    # https://stackoverflow.com/questions/10127284/overlay-imshow-plots-in-matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import colorConverter
    import matplotlib as mpl

    if axis_handle is None:
        ax = plt.gca()

    time_len = len(piano_roll)
    n_voices = len(piano_roll[0])
    n_colors = len(colors)
    if n_voices > n_colors:
        raise ValueError("Need as many colors as voices! Only gave {} colors for {} voices".format(n_colors, n_voices))
    if ribbons:
        ribbons_traces = ribbons_from_piano_roll(piano_roll, ribbon_type,
                                                 quantized_bin_size)
        from IPython import embed; embed(); raise ValueError()
    else:
       ribbons_traces = None
    # 0 always rest!
    voice_storage = np.zeros((time_len, pitch_top, n_voices))

    for v in range(n_voices):
        pitch_offset_values = [piano_roll[i][v] for i in range(time_len)]

        for n, pov in enumerate(pitch_offset_values):
            voice_storage[n, pov, v] = 255.

    cmaps = [mpl.colors.LinearSegmentedColormap.from_list("my_cmap_{}".format(v), ["white", c], 256)
             for c, v in zip(colors, list(range(n_voices)))]

    for cmap in cmaps:
        cmap._init()
        # lazy way to make zeros of right size
        alphas = np.linspace(0., 0.6, cmap.N + 3)
        cmap._lut[:, -1] = alphas

    nz = np.where(voice_storage != 0.)[1]
    nz = nz[nz >= pitch_bot]
    nz = nz[nz <= pitch_top]
    if autorange:
        mn = nz.min() - 6
        mx = nz.max() + 1 + 6
    else:
        if show_rest_channel:
            mn = 0
        else:
            mn = pitch_bot
        mx = pitch_top + 1

    for v in range(n_voices):
        ax.imshow(voice_storage[:, :, v].T, cmap=cmaps[v])
    ax.set_ylim([mn, mx])
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Pitch")

    def autoaspect(x_range, y_range):
        """
        The aspect to make a plot square with ax.set_aspect in Matplotlib
        """
        mx = max(x_range, y_range)
        mn = min(x_range, y_range)
        if x_range <= y_range:
            return mx / float(mn)
        else:
            return mn / float(mx)
    asp = autoaspect(mx - mn, autoscale_ratio * len(voice_storage))
    ax.set_aspect(asp)
    patch_list = [mpatches.Patch(color=c, alpha=.6, label="Voice {}".format(v)) for c, v in zip(colors, list(range(n_voices)))]
    ax.legend(handles=patch_list, bbox_to_anchor=(0., -.3, 1., .102), loc=1,
              ncol=1, borderaxespad=0.)
    if show:
        plt.show()
    return ribbons_traces


# https://raw.githubusercontent.com/josquin-research-project/Jos/6b34b195211b2ef563d30b36567f376b3189a561/Jos2721-La_Bernardina.krn
p = converter.parse("Jos2721-La_Bernardina.krn")
r = music21_to_pitch_duration(p)
parts, _, parts_durations = r
quantized_bin_size = 0.5
pr = pitch_and_duration_to_piano_roll(parts, parts_durations, quantized_bin_size)
quantized_to_pretty_midi([pr],
                         quantized_bin_size,
                         save_dir="samples",
                         name_tag="sample_{}.mid",
                         max_hold_bars=2,
                         default_quarter_length=110,
                         voice_params="woodwinds")
plot_piano_roll(pr, quantized_bin_size)