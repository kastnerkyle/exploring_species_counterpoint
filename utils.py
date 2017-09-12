from __future__ import print_function
import subprocess
from music21 import converter
import os
import numpy as np
import fractions

# Convenience function to reuse the defined env
def pwrap(args, shell=False):
    p = subprocess.Popen(args, shell=shell, stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                         universal_newlines=True)
    return p

# Print output
# http://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
def execute(cmd, shell=False):
    popen = pwrap(cmd, shell=shell)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line

    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def pe(cmd, shell=True):
    """
    Print and execute command on system
    """
    ret = []
    for line in execute(cmd, shell=shell):
        ret.append(line)
        print(line, end="")
    return ret


def music21_extract(p):
    """
    Taken from pthbldr

    Takes in a Music21 score, and outputs dict
    """
    parts = []
    parts_times = []
    parts_delta_times = []
    parts_extras = []
    parts_time_signatures = []
    parts_key_signatures = []
    for i, pi in enumerate(p.parts):
        part = []
        part_time = []
        part_delta_time = []
        part_extras = []
        total_time = 0
        ts = pi.stream().flat.timeSignature
        ks = pi.stream().flat.keySignature
        if len(ks.alteredPitches) == 0:
            parts_key_signatures.append([0])
        else:
            parts_key_signatures.append([ks.sharps])

        parts_time_signatures.append((ts.numerator, ts.denominator))
        for n in pi.stream().flat.notesAndRests:
            if n.isRest:
                part.append(0)
            else:
                try:
                    part.append(n.midi)
                except AttributeError:
                    continue
            if n.tie is not None:
                if n.tie.type == "start":
                    part_extras.append(1)
                elif n.tie.type == "continue":
                    part_extras.append(2)
                elif n.tie.type == "stop":
                    part_extras.append(3)
                else:
                   print("another type of tie?")
                   from IPython import embed; embed(); raise ValueError()
            elif len(n.expressions) > 0:
                print("trill or fermata?")
                from IPython import embed; embed(); raise ValueError()
            else:
                part_extras.append(0)

            part_time.append(total_time + n.duration.quarterLength)
            total_time = part_time[-1]
            part_delta_time.append(n.duration.quarterLength)
        parts.append(part)
        parts_times.append(part_time)
        parts_delta_times.append(part_delta_time)
        parts_extras.append(part_extras)
    return {"parts": parts,
            "parts_times": parts_times,
            "parts_delta_times": parts_delta_times,
            "parts_extras": parts_extras,
            "parts_time_signatures": parts_time_signatures,
            "parts_key_signatures": parts_key_signatures}


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


# rough guide https://www.python-course.eu/python_scores.php
def plot_lilypond(upper_voices, lower_voices=None, own_staves=False,
                  key_signatures=None,
                  time_signatures=None,
                  fpath="tmp.ly",
                  title="Tmp", composer="Tmperstein", tagline="Copyright:?",
                  x_bounds=(0, None), y_bounds=(15, None)):
    """
    Expects upper_voices and lower_voices to be list of list

    Needs lilypond, and pdf2svg installed (sudo apt-get install pdf2svg)
    """
    if len(upper_voices) > 1:
        if lower_voices == None and own_staves==False:
            raise ValueError("Multiple voices in upper staff with own_staves=False")
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    # need to align them T_T
    # for now assume 4/4
    pre = '\\version "2.12.3"'
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_names = ["\key f \major", "\key g \minor",  "\key c \minor",
                        "\key f \minor", "\key bes \minor", "\key ees \minor",
                        "\key aes \minor"]
    minus_keys_flats = minus_keys_flats[::-1]
    minus_keys_names = minus_keys_names[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    plus_keys_names = ["\key g \major", "\key d \major",  "\key a \major",
                       "\key e \major", "\key b \major", "\key fis \major",
                       "\key cis \major"]
    trange = len(upper_voices)
    if lower_voices is not None:
        trange += len(lower_voices)
    if key_signatures is None:
        key_signatures = [[0] for i in range(trange)]
    if time_signatures is None:
        time_signatures = [(4, 1) for i in range(trange)]
    assert len(key_signatures) == trange
    assert len(time_signatures) == trange

    if own_staves == False:
        upper_staff = ""
        lower_staff = ""

        for n, uv in enumerate(upper_voices):
            ksi = key_signatures[n][0]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                upper_staff += key_name + " "
            for u in uv:
                upper_staff += u + " "

        if lower_voices is not None:
            for n, lv in lower_voices:
                n_offset = n + len(upper_voices)
                ksi = key_signatures[n_offset][0]
                if ksi != 0:
                    if ksi < 0:
                        key_name = minus_keys_names[ksi]
                    else:
                        assert ksi - 1 >= 0
                        key_name = plus_keys_names[ksi - 1]
                    lower_staff += key_name + " "
                for l in lv:
                    lower_staff += l + " "

        staff = "{\n\\new PianoStaff << \n"
        staff += "  \\new Staff {" + upper_staff + "}\n"
        if lower_staff != "":
            staff += "  \\new Staff { \clef bass " + lower_staff + "}\n"
        staff += ">>\n}\n"
    else:
        if lower_voices is not None:
            raise ValueError("Put all voices into list of list upper_voices!")
        staff = "{\n\\new StaffGroup << \n"
        for n, v in enumerate(upper_voices):
            this_staff = ""
            ksi = key_signatures[n][0]
            if ksi != 0:
                if ksi < 0:
                    key_name = minus_keys_names[ksi]
                else:
                    assert ksi - 1 >= 0
                    key_name = plus_keys_names[ksi - 1]
                this_staff += key_name + " "
            for vi in v:
                this_staff += vi + " "
            staff += "  \\new Staff {" + this_staff + "}\n"
        staff += ">>\n}\n"
    title = """\header {{
title = "{}"
composer = "{}"
tagline = "{}"
}}""".format(title, composer, tagline)

    final_ly = pre + staff + title
    with open(fpath, "w") as f:
        f.write(final_ly)

    # also make the pdf?
    # pe("lilypond {}".format(fpath))
    pe("lilypond -fpng {}".format(fpath))
    if len(fpath.split(os.sep)) == 1:
        flist = os.listdir(os.getcwd())
    else:
        flist = os.listdir(str(os.sep).join(fpath.split(os.sep)[:-1]))
    valid_files_name = ".".join(fpath.split(os.sep)[-1].split(".")[:-1])
    flist = [fl for fl in flist if valid_files_name in fl]
    # hardcode to only show 1 page for now...
    flist = [fl for fl in flist if "page1" in fl or "page" not in fl]
    latest_file = max(flist, key=os.path.getctime)
    img = mpimg.imread(latest_file)
    img = img[y_bounds[0]:y_bounds[1], x_bounds[0]:x_bounds[1]]
    plt.imshow(img)
    plt.show()


def map_midi_pitches_to_lilypond(pitches, key_signatures=None):
    # takes in list of list
    # 0 = rest
    # 12 = C0
    # 24 = C1
    # 36 = C2
    # 48 = C3
    # 60 = C4
    # 72 = C5
    # 84 = C6

    # accidentals are key dependent! oy vey
    sharp_notes = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]
    flat_notes =  ["c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "ces"]
    octave_map = [",,,", ",,", ",", "", "'", "''", "'''"]
    minus_keys_flats = ["b", "e", "a", "d", "g", "c", "f"]
    minus_keys_flats = minus_keys_flats[::-1]
    plus_keys_sharps = ["f", "c", "g", "d", "a", "e", "b"]
    rest = "r"
    lily_str_lists = []
    if key_signatures is None:
        key_signatures = [[0] for i in range(len(pitches))]
    use_voice_notes = [sharp_notes if key_signatures[i][0] >= 0 else flat_notes
                       for i in range(len(pitches))]
    assert len(key_signatures) == len(pitches)
    for n, (ks, pv) in enumerate(zip(key_signatures, pitches)):
        use_notes = use_voice_notes[n]
        note_str = [use_notes[int(pvi % 12)] if pvi != 0 else rest for pvi in pv]
        octave_str = [octave_map[int(pvi // 12)] if pvi != 0 else "" for pvi in pv]
        str_list = [ns + os for ns, os in zip(note_str, octave_str)]
        lily_str_lists.append(str_list)
    return lily_str_lists


def map_midi_durations_to_lilypond(durations, extras):
    # assumed to be relative lengths from quarter note?
    # do I need to make Fraction objects?
    # default is quarter note
    def ff(f):
        return fractions.Fraction(f)

    duration_map = {ff(8.): "\\breve",
                    ff(6.): "1.",
                    ff(4.): "1",
                    ff(3.): "2.",
                    ff(2.): "2",
                    ff(1.): "4",
                    ff(.5): "8",
                    ff(.25): "16",
                    ff(.125): "32",
                    ff(.0625): "64"}

    lily_str_lists = []
    assert len(durations) == len(extras)
    for dv, ev in zip(durations, extras):
        str_list = []
        assert len(dv) == len(ev)
        for dvi, evi in zip(dv, ev):
            try:
                frac_dvi = duration_map[ff(dvi)]
                if evi != 0:
                   if evi == 1 or evi == 2:
                       frac_dvi += "~"
                str_list.append(frac_dvi)
            except KeyError:
                raise KeyError("No known mapping for duration {}".format(dvi))
        lily_str_lists.append(str_list)
    return lily_str_lists


def pitches_and_durations_to_lilypond_notation(pitches, durations, extras,
                                               key_signatures=None):
    lilypitches = map_midi_pitches_to_lilypond(pitches, key_signatures=key_signatures)
    lilydurs = map_midi_durations_to_lilypond(durations, extras)
    assert len(lilypitches) == len(lilydurs)
    lilycomb = []
    for lp, ld in zip(lilypitches, lilydurs):
        assert len(lp) == len(ld)
        lc = [lpi + ldi for lpi, ldi in zip(lp, ld)]
        lilycomb.append(lc)
    return lilycomb


def plot_pitches_and_durations(pitches, durations, extras,
                               time_signatures=None,
                               key_signatures=None):
    # map midi pitches to lilypond ones... oy
    voices = pitches_and_durations_to_lilypond_notation(pitches, durations, extras, key_signatures=key_signatures)
    #plot_lilypond([voices[0]])
    #plot_lilypond([voices[0]], [voices[-1]])
    #plot_lilypond([voices[0]], [voices[-1]], own_staves=True)
    plot_lilypond(voices, own_staves=True,
                  time_signatures=time_signatures,
                  key_signatures=key_signatures)
    raise ValueError("b")


"""
p = converter.parse("Jos2721-La_Bernardina.krn")
"""
p = converter.parse("Jos2835-Une_musque_de_Buscaya.krn")

r = music21_extract(p)
parts = r["parts"]
parts_durations = r["parts_delta_times"]
parts_extras = r["parts_extras"]
parts_time_signatures = r["parts_time_signatures"]
parts_key_signatures = r["parts_key_signatures"]
plot_pitches_and_durations(parts, parts_durations, parts_extras,
                           time_signatures=parts_time_signatures,
                           key_signatures=parts_key_signatures)


#plot_lilypond([["<c'>", "<e'>", "<g'>", "<a'>"]], [["<c>", "<e>", "<g>", "<a>"]])
#plot_lilypond([["<c'>", "<e'>", "<g'>", "<a'>"], ["<c''>", "<e''>", "<g''>", "<a''>"]], [["<c>", "<e>", "<g>", "<a>"], ["<c,>", "<e,>", "<g,>", "<a,>"]])
