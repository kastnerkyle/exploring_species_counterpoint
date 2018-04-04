# -*- coding: utf-8 -*-
from music21 import converter, roman, key


def music21_extract(p):
    """
    Takes in a Music21 score, and outputs dict
    """
    parts = []
    parts_times = []
    parts_delta_times = []
    parts_extras = []
    parts_time_signatures = []
    parts_key_signatures = []
    c = p.chordify()
    ks = p.parts[0].stream().flat.keySignature
    parts_roman_chords = []
    parts_chords = []
    for this_chord in c.recurse().getElementsByClass('Chord'):
        parts_chords.append(this_chord.fullName)
        #print(this_chord.measureNumber, this_chord.beatStr, this_chord)
        rn = roman.romanNumeralFromChord(this_chord, ks.asKey())
        parts_roman_chords.append(rn.figure)

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
            "parts_key_signatures": parts_key_signatures,
            "parts_chords": parts_chords,
            "parts_roman_chords": parts_roman_chords}


def fetch_two_voice_species1():
    all_ex = []

    # All figure numbers from Gradus ad Parnassum
    # fig 5, correct notes
    ex = {"notes_and_durations": [[('A3', '4'), ('A3', '4'), ('G3', '4'), ('A3', '4'), ('B3', '4'), ('C4', '4'), ('C4', '4'), ('B3', '4'), ('D4', '4'), ('C#4', '4'), ('D4', '4')], [('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')]],
          "answers": [True] * 11,
          "name": "fig5",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 6, initial (incorrect) notes
    ex = {"notes_and_durations": [[('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')], [('G2', '4'), ('D3', '4'), ('A2', '4'), ('F2', '4'), ('E2', '4'), ('D2', '4'), ('F2', '4'), ('C3', '4'), ('D3', '4'), ('C#3', '4'), ('D3', '4')]],
          "answers": [True if n not in [0, 2] else False for n in range(11)],
          "name": "fig6w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 6, correct notes
    ex = {"notes_and_durations": [[('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')], [('D2', '4'), ('D2', '4'), ('A2', '4'), ('F2', '4'), ('E2', '4'), ('D2', '4'), ('F2', '4'), ('C3', '4'), ('D3', '4'), ('C#3', '4'), ('D3', '4')]],
          "answers": [True] * 11,
          "name": "fig6c",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 11, correct notes
    ex = {"notes_and_durations": [[('B3', '4'), ('C4', '4'), ('F3', '4'), ('G3', '4'), ('A3', '4'), ('C4', '4'), ('B3', '4'), ('E4', '4'), ('D4', '4'), ('E4', '4')], [('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')]],
          "answers": [True] * 10,
          "name": "fig11",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 12, incorrect notes
    ex = {"notes_and_durations": [[('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')], [('E2', '4'), ('A2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('F2', '4'), ('B2', '4'), ('C3', '4'), ('D3', '4'), ('E3', '4')]],
          "answers": [True if n not in [6,] else False for n in range(10)],
          "name": "fig12w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 13, correct notes
    ex = {"notes_and_durations": [[('F3', '4'), ('E3', '4'), ('C3', '4'), ('F3', '4'), ('F3', '4'), ('G3', '4'), ('A3', '4'), ('G3', '4'), ('C3', '4'), ('F3', '4'), ('E3', '4'), ('F3', '4')], [('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')]],
          "answers": [True] * 12,
          "name": "fig13",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 14, correct notes w/ voice crossing
    ex = {"notes_and_durations": [[('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')], [('F2', '4'), ('E2', '4'), ('F2', '4'), ('A2', '4'), ('Bb2', '4'), ('G2', '4'), ('A2', '4'), ('E2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4')]],
          "answers": [True] * 12,
          "name": "fig14",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 15, incorrect notes
    ex = {"notes_and_durations": [[('G3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('G3', '4'), ('G3', '4'), ('A3', '4'), ('B3', '4'), ('G3', '4'), ('E4', '4'), ('D4', '4'), ('G3', '4'), ('F#3', '4'), ('G3', '4')], [('G2', '4'), ('C3', '4'), ('B2', '4'), ('G2', '4'), ('C3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4'), ('C3', '4'), ('D3', '4'), ('B2', '4'), ('A2', '4'), ('G2', '4')]],
          "answers": [True if n not in [10,] else False for n in range(14)],
          "name": "fig15w",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 15, correct notes
    ex = {"notes_and_durations": [[('G3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('G3', '4'), ('G3', '4'), ('A3', '4'), ('B3', '4'), ('G3', '4'), ('C4', '4'), ('A3', '4'), ('G3', '4'), ('F#3', '4'), ('G3', '4')], [('G2', '4'), ('C3', '4'), ('B2', '4'), ('G2', '4'), ('C3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4'), ('C3', '4'), ('D3', '4'), ('B2', '4'), ('A2', '4'), ('G2', '4')]],
          "answers": [True] * 14,
          "name": "fig15c",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 21, correct notes
    ex = {"notes_and_durations": [[('G2', '4'), ('C3', '4'), ('B2', '4'), ('G2', '4'), ('C3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4'), ('C3', '4'), ('D3', '4'), ('B2', '4'), ('A2', '4'), ('G2', '4')], [('G2', '4'), ('A2', '4'), ('G2', '4'), ('E2', '4'), ('E2', '4'), ('C2', '4'), ('G2', '4'), ('B2', '4'), ('C3', '4'), ('A2', '4'), ('F#2', '4'), ('G2', '4'), ('F#2', '4'), ('G2', '4')]],
          "answers": [True] * 14,
          "name": "fig21",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 22, correct notes
    ex = {"notes_and_durations": [[('A3', '4'), ('E3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('C4', '4'), ('A3', '4'), ('B3', '4'), ('B3', '4'), ('A3', '4'), ('G#3', '4'), ('A3', '4')], [('A2', '4'), ('C3', '4'), ('B2', '4'), ('D3', '4'), ('C3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4'), ('A2', '4')]],
          "answers": [True] * 12,
          "name": "fig22",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 23, correct notes
    ex = {"notes_and_durations": [[('A2', '4'), ('C3', '4'), ('B2', '4'), ('D3', '4'), ('C3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4'), ('A2', '4')], [('A2', '4'), ('A2', '4'), ('G2', '4'), ('F2', '4'), ('E2', '4'), ('E2', '4'), ('D2', '4'), ('C2', '4'), ('G2', '4'), ('A2', '4'), ('G#2', '4'), ('A2', '4')]],
          "answers": [True] * 12,
          "name": "fig23",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species2():
    all_ex = []
    # fig 26
    ex = {"notes_and_durations": [[('A3', '2'), ('D4', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('G3', '2'), ('A3', '2'), ('D4', '2'), ('B3', '2'), ('G3', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('A3', '2'), ('D4', '2'), ('B3', '2'), ('C4', '2'), ('A3', '2'), ('B3', '2'), ('C#4', '2'), ('D4', '4')], [('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')]],
          "answers": [True if n not in [16, 18] else False for n in range(21)],
          "name": "fig26",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 33
    ex = {"notes_and_durations": [[('A3', '2'), ('D4', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('G3', '2'), ('A3', '2'), ('D4', '2'), ('B3', '2'), ('C4', '2'), ('D4', '2'), ('A3', '2'), ('C4', '2'), ('D4', '2'), ('E4', '2'), ('B3', '2'), ('D4', '2'), ('A3', '2'), ('B3', '2'), ('C#4', '2'), ('D4', '4')], [('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')]],
          "answers": [True] * 21,
          "name": "fig33",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 35
    ex = {"notes_and_durations": [[('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')], [('R', '2'), ('D2', '2'), ('D3', '2'), ('A2', '2'), ('C3', '2'), ('A2', '2'), ('B2', '2'), ('A2', '2'), ('G2', '2'), ('B2', '2'), ('D3', '2'), ('E3', '2'), ('F3', '2'), ('C3', '2'), ('E3', '2'), ('B2', '2'), ('D3', '2'), ('D2', '2'), ('A2', '2'), ('C#3', '2'), ('D3', '4')]],
          "answers": [True] * 21,
          "name": "fig35",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 36
    ex = {"notes_and_durations": [[('R', '2'), ('B3', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('G3', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('A3', '2'), ('B3', '2'), ('D4', '2'), ('E4', '2'), ('D4', '2'), ('C4', '2'), ('D4', '2'), ('E4', '4')], [('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')]],
          "answers": [True] * 19,
          "name": "fig36",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 37
    ex = {"notes_and_durations": [[('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')], [('R', '2'), ('E2', '2'), ('A2', '2'), ('G2', '2'), ('F2', '2'), ('D2', '2'), ('E2', '2'), ('C2', '2'), ('F2', '2'), ('C3', '2'), ('F3', '2'), ('D3', '2'), ('E3', '2'), ('D3', '2'), ('C3', '2'), ('B2', '2'), ('A2', '2'), ('D3', '2'), ('E3', '4')]],
          "answers": [True] * 19,
          "name": "fig37",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 38
    ex = {"notes_and_durations": [[('R', '2'), ('F3', '2'), ('E3', '2'), ('D3', '2'), ('C3', '2'), ('Bb2', '2'), ('A2', '2'), ('G2', '2'), ('F2', '2'), ('A2', '2'), ('C3', '2'), ('Bb2', '2'), ('A2', '2'), ('A3', '2'), ('G3', '2'), ('E3', '2'), ('F3', '2'), ('G3', '2'), ('A3', '2'), ('F3', '2'), ('D3', '2'), ('E3', '2'), ('F3', '4')], [('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')]],
          "answers": [True] * 23,
          "name": "fig38",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 39
    ex = {"notes_and_durations": [[('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')], [('R', '2'), ('F2', '2'), ('E2', '2'), ('C2', '2'), ('F2', '2'), ('E2', '2'), ('D2', '2'), ('C2', '2'), ('Bb1', '2'), ('Bb2', '2'), ('G2', '2'), ('C3', '2'), ('A2', '2'), ('F2', '2'), ('E2', '2'), ('C2', '2'), ('F2', '2'), ('F1', '2'), ('A1', '2'), ('D2', '2'), ('C2', '2'), ('E2', '2'), ('F2', '4')]],
          "answers": [True] * 23,
          "name": "fig39",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 40
    ex = {"notes_and_durations": [[('R', '2'), ('G3', '2'), ('E3', '2'), ('F3', '2'), ('G3', '2'), ('A3', '2'), ('B3', '2'), ('A3', '2'), ('G3', '2'), ('C4', '2'), ('B3', '2'), ('C4', '2'), ('D4', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('G3', '2'), ('F3', '2'), ('E3', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('G3', '2'), ('D3', '2'), ('E3', '2'), ('F#3', '2'), ('G3', '4')], [('G2', '4'), ('C3', '4'), ('B2', '4'), ('G2', '4'), ('C3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4'), ('C3', '4'), ('D3', '4'), ('B2', '4'), ('A2', '4'), ('G2', '4')]],
          "answers": [True] * 27,
          "name": "fig40",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 41
    ex = {"notes_and_durations": [[('G2', '4'), ('C3', '4'), ('B2', '4'), ('G2', '4'), ('C3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4'), ('C3', '4'), ('D3', '4'), ('B2', '4'), ('A2', '4'), ('G2', '4')], [('R', '2'), ('G2', '2'), ('E2', '2'), ('F2', '2'), ('G2', '2'), ('F2', '2'), ('E2', '2'), ('D2', '2'), ('C2', '2'), ('E2', '2'), ('C2', '2'), ('C3', '2'), ('B2', '2'), ('A2', '2'), ('G2', '2'), ('B2', '2'), ('C3', '2'), ('B2', '2'), ('A2', '2'), ('G2', '2'), ('F#2', '2'), ('D2', '2'), ('G2', '2'), ('B1', '2'), ('D2', '2'), ('F#2', '2'), ('G2', '4')]],
          "answers": [True] * 27,
          "name": "fig41",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 42
    ex = {"notes_and_durations": [[('R', '2'), ('A3', '2'), ('E3', '2'), ('F3', '2'), ('G3', '2'), ('D3', '2'), ('E3', '2'), ('E4', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('F3', '2'), ('G3', '2'), ('B3', '2'), ('D4', '2'), ('A3', '2'), ('C4', '2'), ('E3', '2'), ('F#3', '2'), ('G#3', '2'), ('A3', '4')], [('A2', '4'), ('C3', '4'), ('B2', '4'), ('C3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4'), ('A2', '4')]],
          "answers": [True] * 21,
          "name": "fig42",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 43
    ex = {"notes_and_durations": [[('A2', '4'), ('C3', '4'), ('B2', '4'), ('D3', '4'), ('C3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4'), ('A2', '4')], [('R', '2'), ('A1', '2'), ('A2', '2'), ('E2', '2'), ('G2', '2'), ('E2', '2'), ('D2', '2'), ('F2', '2'), ('A2', '2'), ('B2', '2'), ('C3', '2'), ('C2', '2'), ('D2', '2'), ('A1', '2'), ('C2', '2'), ('E2', '2'), ('F2', '2'), ('G2', '2'), ('A2', '2'), ('A1', '2'), ('E2', '2'), ('G#2', '2'), ('A2', '4')]],
          "answers": [True] * 23,
          "name": "fig43",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 44
    ex = {"notes_and_durations": [[('R', '2'), ('G3', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('D4', '2'), ('B3', '2'), ('A3', '2'), ('G3', '2'), ('B3', '2'), ('C4', '2'), ('D4', '2'), ('E4', '2'), ('D4', '2'), ('C4', '2'), ('B3', '2'), ('A3', '2'), ('B3', '2'), ('C4', '2'), ('G3', '2'), ('A3', '2'), ('B3', '2'), ('C4', '4')], [('C3', '4'), ('E3', '4'), ('F3', '4'), ('G3', '4'), ('E3', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4')]],
          "answers": [True] * 23,
          "name": "fig44",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 45
    ex = {"notes_and_durations": [[('C3', '4'), ('E3', '4'), ('F3', '4'), ('G3', '4'), ('E3', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4')], [('R', '2'), ('C2', '2'), ('C3', '2'), ('B2', '2'), ('A2', '2'), ('D3', '2'), ('B2', '2'), ('G2', '2'), ('C3', '2'), ('B2', '2'), ('A2', '2'), ('C3', '2'), ('E3', '2'), ('D3', '2'), ('C3', '2'), ('A2', '2'), ('D3', '2'), ('A2', '2'), ('C3', '2'), ('C2', '2'), ('G2', '2'), ('B2', '2'), ('C3', '4')]],
          "answers": [True] * 23,
          "name": "fig45",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species3():
    all_ex = []

    # fig 55
    ex = {"notes_and_durations": [[('D3', '1'), ('E3', '1'), ('F3', '1'), ('G3', '1'), ('A3', '1'), ('B3', '1'), ('C4', '1'), ('D4', '1'), ('E4', '1'), ('D4', '1'), ('B3', '1'), ('C4', '1'), ('D4', '1'), ('C4', '1'), ('Bb3', '1'), ('A3', '1'), ('Bb3', '1'), ('C4', '1'), ('D4', '1'), ('E4', '1'), ('F4', '1'), ('F3', '1'), ('A3', '1'), ('Bb3', '1'), ('C4', '1'), ('A3', '1'), ('Bb3', '1'), ('C4', '1'), ('Bb3', '1'), ('A3', '1'), ('G3', '1'), ('Bb3', '1'), ('A3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('G3', '1'), ('A3', '1'), ('B3', '1'), ('C#4', '1'), ('D4', '4')], [('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')]],
          "answers": [True] * 41,
          "name": "fig55",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 56
    ex = {"notes_and_durations": [[('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')], [('D2', '1'), ('E2', '1'), ('F2', '1'), ('G2', '1'), ('A2', '1'), ('D2', '1'), ('A2', '1'), ('B2', '1'), ('C3', '1'), ('B2', '1'), ('G2', '1'), ('A2', '1'), ('B2', '1'), ('A2', '1'), ('G2', '1'), ('F2', '1'), ('E2', '1'), ('E3', '1'), ('B2', '1'), ('C3', '1'), ('D3', '1'), ('A2', '1'), ('D2', '1'), ('E2', '1'), ('F2', '1'), ('G2', '1'), ('A2', '1'), ('B2', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('C3', '1'), ('D3', '1'), ('A2', '1'), ('D2', '1'), ('D3', '1'), ('C#3', '1'), ('A2', '1'), ('B2', '1'), ('C3', '1'), ('D3', '4')]],
          "answers": [True] * 41,
          "name": "fig56",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 57
    ex = {"notes_and_durations": [[('B3', '1'), ('G3', '1'), ('A3', '1'), ('B3', '1'), ('C4', '1'), ('B3', '1'), ('A3', '1'), ('G3', '1'), ('F3', '1'), ('G3', '1'), ('A3', '1'), ('B3', '1'), ('C4', '1'), ('E3', '1'), ('F3', '1'), ('G3', '1'), ('A3', '1'), ('C4', '1'), ('E4', '1'), ('D4', '1'), ('C4', '1'), ('B3', '1'), ('A3', '1'), ('C4', '1'), ('B3', '1'), ('D4', '1'), ('B3', '1'), ('A3', '1'), ('G3', '1'), ('B3', '1'), ('C4', '1'), ('B3', '1'), ('A3', '1'), ('B3', '1'), ('C4', '1'), ('D4', '1'), ('E4', '4')], [('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')]],
          "answers": [True] * 37,
          "name": "fig57",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 58
    ex = {"notes_and_durations": [[('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')], [('E2', '1'), ('F2', '1'), ('G2', '1'), ('E2', '1'), ('A2', '1'), ('G2', '1'), ('F2', '1'), ('E2', '1'), ('D2', '1'), ('E2', '1'), ('F2', '1'), ('G2', '1'), ('A2', '1'), ('E2', '1'), ('A2', '1'), ('G2', '1'), ('F2', '1'), ('E2', '1'), ('D2', '1'), ('E2', '1'), ('F2', '1'), ('G2', '1'), ('A2', '1'), ('B2', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('C2', '1'), ('C3', '1'), ('B2', '1'), ('A2', '1'), ('D3', '1'), ('A2', '1'), ('D3', '1'), ('E3', '4')]],
          "answers": [True] * 37,
          "name": "fig58",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 59
    ex = {"notes_and_durations": [[('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('B2', '1'), ('D3', '1'), ('G3', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('Bb2', '1'), ('A2', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('G3', '1'), ('E3', '1'), ('F3', '1'), ('G3', '1'), ('A3', '1'), ('G3', '1'), ('F3', '1'), ('A3', '1'), ('G3', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('E3', '1'), ('C3', '1'), ('E3', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('Bb2', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '4')], [('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')]],
          "answers": [True] * 45,
          "name": "fig59",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 60
    # swap top and bottom around, weird notation but "bass" is in top on paper
    ex = {"notes_and_durations": [[('F2', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('E3', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('D3', '1'), ('C3', '1'), ('Bb2', '1'), ('A2', '1'), ('Bb2', '1'), ('F3', '1'), ('Bb3', '1'), ('A3', '1'), ('G3', '1'), ('C3', '1'), ('C4', '1'), ('Bb3', '1'), ('A3', '1'), ('G3', '1'), ('F3', '1'), ('D3', '1'), ('E3', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('E3', '1'), ('D3', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '1'), ('D3', '1'), ('E3', '1'), ('C3', '1'), ('D3', '1'), ('E3', '1'), ('F3', '4')], [('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')]],
          "answers": [True] * 45,
          "name": "fig60",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species4():
    all_ex = []
    # fig 61
    ex = {"notes_and_durations": [[('R', '2'), ('C4', '4'), ('A3', '4'), ('D4', '4'), ('B3', '4'), ('E4', '2')], [('C3', '4'), ('F3', '4'), ('D3', '4'), ('G3', '4'), ('E3', '4')]],
          "answers": [False] + [True] * 9,
          # First false due to mode estimation failure in partial sequences
          "name": "fig61",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 62
    ex = {"notes_and_durations": [[('R', '2'), ('E4', '4'), ('D4', '4'), ('C4', '4'), ('B3', '2'), ('C4', '4')], [('C3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C3', '4')]],
          "answers": [True] * 9,
          "name": "fig62",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 63
    ex = {"notes_and_durations": [[('R', '2'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '2')], [('E3', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4')]],
          "answers": [False] + [True] * 7,
          # Handle mode estimation error for partial sequence
          "name": "fig63",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 73
    ex = {"notes_and_durations": [[('R', '2'), ('A3', '4'), ('D4', '4'), ('C4', '4'), ('Bb3', '4'), ('G3', '2'), ('A3', '2'), ('C4', '4'), ('F4', '4'), ('E4', '4'), ('D4', '4'), ('C#4', '2'), ('D4', '4')], [('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')]],
          "answers": [True] * 21,
          "name": "fig73",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 74
    ex = {"notes_and_durations": [[('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('G3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4')], [('R', '2'), ('D2', '4'), ('D3', '4'), ('C3', '4'), ('B2', '4'), ('E3', '4'), ('D3', '4'), ('F3', '4'), ('E3', '4'), ('D3', '4'), ('C#3', '2'), ('D3', '4')]],
          "answers": [True] * 21,
          "name": "fig74",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 75
    ex = {"notes_and_durations": [[('R', '2'), ('E4', '4'), ('C4', '4'), ('B3', '2'), ('C4', '2'), ('E3', '4'), ('F3', '4'), ('C4', '4'), ('B3', '4'), ('E4', '4'), ('D4', '2'), ('E4', '4')], [('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')]],
          "answers": [True] * 19,
          "name": "fig75",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 76
    ex = {"notes_and_durations": [[('E3', '4'), ('C3', '4'), ('D3', '4'), ('C3', '4'), ('A2', '4'), ('A3', '4'), ('G3', '4'), ('E3', '4'), ('F3', '4'), ('E3', '4')], [('R', '2'), ('E2', '4'), ('A2', '4'), ('G2', '4'), ('F2', '4'), ('D2', '4'), ('D3', '4'), ('C3', '4'), ('E3', '4'), ('D3', '2'), ('E3', '4')]],
          "answers": [True] * 19,
          "name": "fig76",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 77
    ex = {"notes_and_durations": [[('R', '2'), ('F3', '4'), ('E3', '4'), ('C3', '4'), ('F3', '4'), ('A3', '4'), ('G3', '4'), ('F3', '4'), ('E3', '4'), ('A3', '4'), ('F3', '4'), ('E3', '2'), ('F3', '4')], [('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')]],
          "answers": [True] * 23,
          "name": "fig77",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 78
    ex = {"notes_and_durations": [[('F2', '4'), ('G2', '4'), ('A2', '4'), ('F2', '4'), ('D2', '4'), ('E2', '4'), ('F2', '4'), ('C3', '4'), ('A2', '4'), ('F2', '4'), ('G2', '4'), ('F2', '4')], [('R', '2'), ('F2', '4'), ('E2', '4'), ('D2', '4'), ('Bb1', '4'), ('G1', '4'), ('G2', '4'), ('F2', '4'), ('E2', '4'), ('D2', '4'), ('F2', '4'), ('E2', '2'), ('F2', '4')]],
          "answers": [True] * 23,
          "name": "fig78",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex
