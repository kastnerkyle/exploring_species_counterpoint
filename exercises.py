# -*- coding: utf-8 -*-

def fetch_two_voice_species1():
    all_ex = []

    # All figure numbers from Gradus ad Parnassum
    # fig 5, correct notes
    ex = {"notes": [["A3", "A3", "G3", "A3", "B3", "C4", "C4", "B3", "D4", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True] * 11,
          "name": "fig5",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 6, initial (incorrect) notes
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["G2", "D3", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True if n not in [0, 2] else False for n in range(11)],
          "name": "fig6w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 6, correct notes
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["D2", "D2", "A2", "F2", "E2", "D2", "F2", "C3", "D3", "C#3", "D3"]],
          "durations": [["4"] * 11, ["4"] * 11],
          "answers": [True] * 11,
          "name": "fig6c",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 11, correct notes
    ex = {"notes": [["B3", "C4", "F3", "G3", "A3", "C4", "B3", "E4", "D4", "E4"],
                    ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["4"] * 10, ["4"] * 10],
          "answers": [True] * 10,
          "name": "fig11",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 12, incorrect notes
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["E2", "A2", "D2", "E2", "F2", "F2", "B2", "C3", "D3", "E3"]],
          "durations": [["4"] * 10, ["4"] * 10],
          "answers": [True if n not in [6,] else False for n in range(10)],
          "name": "fig12w",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 13, correct notes
    ex = {"notes": [["F3", "E3", "C3", "F3", "F3", "G3", "A3", "G3", "C3", "F3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig13",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 14, correct notes w/ voice crossing
    ex = {"notes": [["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"],
                    ["F2", "E2", "F2", "A2", "Bb2", "G2", "A2", "E2", "F2", "D2", "E2", "F2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig14",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 15, incorrect notes
    ex = {"notes": [["G3", "E3", "D3", "G3", "G3", "G3", "A3", "B3", "G3", "E4", "D4", "G3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True if n not in [10,] else False for n in range(14)],
          "name": "fig15w",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 15, correct notes
    ex = {"notes": [["G3", "E3", "D3", "G3", "G3", "G3", "A3", "B3", "G3", "C4", "A3", "G3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True] * 14,
          "name": "fig15c",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 21, correct notes
    ex = {"notes": [["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"],
                    ["G2", "A2", "G2", "E2", "E2", "C2", "G2", "B2", "C3", "A2", "F#2", "G2", "F#2", "G2"]],
          "durations": [["4"] * 14, ["4"] * 14],
          "answers": [True] * 14,
          "name": "fig21",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 22, correct notes
    ex = {"notes": [["A3", "E3", "G3", "F3", "E3", "C4", "A3", "B3", "B3", "A3", "G#3", "A3"],
                    ["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig22",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 23, correct notes
    ex = {"notes": [["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"],
                    ["A2", "A2", "G2", "F2", "E2", "E2", "D2", "C2", "G2", "A2", "G#2", "A2"]],
          "durations": [["4"] * 12, ["4"] * 12],
          "answers": [True] * 12,
          "name": "fig23",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species2():
    all_ex = []
    # fig 26
    ex = {"notes": [["A3", "D4", "A3", "B3", "C4", "G3", "A3", "D4", "B3", "G3", "A3", "B3", "C4", "A3", "D4", "B3", "C4", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True if n not in [16, 18] else False for n in range(21)],
          "name": "fig26",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 33
    ex = {"notes": [["A3", "D4", "A3", "B3", "C4", "G3", "A3", "D4", "B3", "C4", "D4", "A3", "C4", "D4", "E4", "B3", "D4", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True] * 21,
          "name": "fig33",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 35
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["R", "D2", "D3", "A2", "C3", "A2", "B2", "A2", "G2", "B2", "D3", "E3", "F3", "C3", "E3", "B2", "D3", "D2", "A2", "C#3", "D3"]],
          "durations": [["4"] * 11, ["2"] * 20 + ["4"]],
          "answers": [True] * 21,
          "name": "fig35",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 36
    ex = {"notes": [["R", "B3", "C4", "B3", "A3", "B3", "C4", "G3", "A3", "B3", "C4", "A3", "B3", "D4", "E4", "D4", "C4", "D4", "E4"],
                    ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["2"] * 18 + ["4"], ["4"] * 10],
          "answers": [True] * 19,
          "name": "fig36",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 37
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["R", "E2", "A2", "G2", "F2", "D2", "E2", "C2", "F2", "C3", "F3", "D3", "E3", "D3", "C3", "B2", "A2", "D3", "E3"]],
          "durations": [["4"] * 10, ["2"] * 18 + ["4"]],
          "answers": [True] * 19,
          "name": "fig37",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 38
    ex = {"notes": [["R", "F3", "E3", "D3", "C3", "Bb2", "A2", "G2", "F2", "A2", "C3", "Bb2", "A2", "A3", "G3", "E3", "F3", "G3", "A3", "F3", "D3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["2"] * 22 + ["4"], ["4"] * 12],
          "answers": [True] * 23,
          "name": "fig38",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 39
    ex = {"notes": [["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"],
                    ["R", "F2", "E2", "C2", "F2", "E2", "D2", "C2", "Bb1", "Bb2", "G2", "C3", "A2", "F2", "E2", "C2", "F2", "F1", "A1", "D2", "C2", "E2", "F2"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig39",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 40
    ex = {"notes": [["R", "G3", "E3", "F3", "G3", "A3", "B3", "A3", "G3", "C4", "B3", "C4", "D4", "C4", "B3", "A3", "G3", "F3", "E3", "C4", "B3", "A3", "G3", "D3", "E3", "F#3", "G3"],
                    ["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"]],
          "durations": [["2"] * 26 + ["4"], ["4"] * 14],
          "answers": [True] * 27,
          "name": "fig40",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 41
    ex = {"notes": [["G2", "C3", "B2", "G2", "C3", "E3", "D3", "G3", "E3", "C3", "D3", "B2", "A2", "G2"],
                    ["R", "G2", "E2", "F2", "G2", "F2", "E2", "D2", "C2", "E2", "C2", "C3", "B2", "A2", "G2", "B2", "C3", "B2", "A2", "G2", "F#2", "D2", "G2", "B1", "D2", "F#2", "G2"]],
          "durations": [["4"] * 14, ["2"] * 26 + ["4"]],
          "answers": [True] * 27,
          "name": "fig41",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 42
    ex = {"notes": [["R", "A3", "E3", "F3", "G3", "D3", "E3", "E4", "C4", "B3", "A3", "F3", "G3", "B3", "D4", "A3", "C4", "E3", "F#3", "G#3", "A3"],
                    ["A2", "C3", "B2", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"]],
          "durations": [["2"] * 20 + ["4"], ["4"] * 11],
          "answers": [True] * 21,
          "name": "fig42",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 43
    ex = {"notes": [["A2", "C3", "B2", "D3", "C3", "E3", "F3", "E3", "D3", "C3", "B2", "A2"],
                    ["R", "A1", "A2", "E2", "G2", "E2", "D2", "F2", "A2", "B2", "C3", "C2", "D2", "A1", "C2", "E2", "F2", "G2", "A2", "A1", "E2", "G#2", "A2"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig43",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 44
    ex = {"notes": [["R", "G3", "C4", "B3", "A3", "D4", "B3", "A3", "G3", "B3", "C4", "D4", "E4", "D4", "C4", "B3", "A3", "B3", "C4", "G3", "A3", "B3", "C4"],
                    ["C3", "E3", "F3", "G3", "E3", "A3", "G3", "E3", "F3", "E3", "D3", "C3"]],
          "durations": [["2"] * 22 + ["4"], ["4"] * 12],
          "answers": [True] * 23,
          "name": "fig44",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 45
    ex = {"notes": [["C3", "E3", "F3", "G3", "E3", "A3", "G3", "E3", "F3", "E3", "D3", "C3"],
                    ["R", "C2", "C3", "B2", "A2", "D3", "B2", "G2", "C3", "B2", "A2", "C3", "E3", "D3", "C3", "A2", "D3", "A2", "C3", "C2", "G2", "B2", "C3"]],
          "durations": [["4"] * 12, ["2"] * 22 + ["4"]],
          "answers": [True] * 23,
          "name": "fig45",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species3():
    all_ex = []

    # fig 55
    ex = {"notes": [["D3", "E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4", "D4", "B3", "C4", "D4", "C4", "Bb3", "A3", "Bb3", "C4", "D4", "E4", "F4", "F3", "A3", "Bb3", "C4", "A3", "Bb3", "C4", "Bb3", "A3", "G3", "Bb3", "A3", "D3", "E3", "F3", "G3", "A3", "B3", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["1"] * 40 + ["4"], ["4"] * 11],
          "answers": [True] * 41,
          "name": "fig55",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 56
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["D2", "E2", "F2", "G2", "A2", "D2", "A2", "B2", "C3", "B2", "G2", "A2", "B2", "A2", "G2", "F2", "E2", "E3", "B2", "C3", "D3", "A2", "D2", "E2", "F2", "G2", "A2", "B2", "C3", "D3", "E3", "C3", "D3", "A2", "D2", "D3", "C#3", "A2", "B2", "C3", "D3"]],
          "durations": [["4"] * 11, ["1"] * 40 + ["4"]],
          "answers": [True] * 41,
          "name": "fig56",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 57
    ex = {"notes": [["B3", "G3", "A3", "B3", "C4", "B3", "A3", "G3", "F3", "G3", "A3", "B3", "C4", "E3", "F3", "G3", "A3", "C4", "E4", "D4", "C4", "B3", "A3", "C4", "B3", "D4", "B3", "A3", "G3", "B3", "C4", "B3", "A3", "B3", "C4", "D4", "E4"],
                     ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["1"] * 36 + ["4"], ["4"] * 10],
          "answers": [True] * 37,
          "name": "fig57",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 58
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["E2", "F2", "G2", "E2", "A2", "G2", "F2", "E2", "D2", "E2", "F2", "G2",
                     "A2", "E2", "A2", "G2", "F2", "E2", "D2", "E2", "F2", "G2", "A2", "B2",
                     "C3", "D3", "E3", "D3", "C3", "C2", "C3", "B2", "A2", "D3", "A2", "D3",
                     "E3"]],
          "durations": [["4"] * 10, ["1"] * 36 + ["4"]],
          "answers": [True] * 37,
          "name": "fig58",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 59
    ex = {"notes": [["F3", "E3", "D3", "C3", "B2", "D3", "G3", "F3", "E3", "D3", "C3", "Bb2",
                     "A2", "C3", "D3", "E3", "F3", "D3", "E3", "F3", "G3", "E3", "F3", "G3",
                     "A3", "G3", "F3", "A3", "G3", "F3", "E3", "D3", "C3", "E3", "C3", "E3",
                     "F3", "E3", "D3", "C3", "Bb2", "C3", "D3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["1"] * 44 + ["4"], ["4"] * 12],
          "answers": [True] * 45,
          "name": "fig59",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 60
    # swap top and bottom around, weird notation but "bass" is in top on paper
    ex = {"notes": [["F2", "F3", "E3", "D3", "E3", "C3", "D3", "E3", "F3", "E3", "D3", "C3",
                     "D3", "C3", "Bb2", "A2", "Bb2", "F3", "Bb3", "A3", "G3", "C3", "C4", "Bb3",
                     "A3", "G3", "F3", "D3", "E3", "C3", "D3", "E3", "F3", "E3", "D3", "C3",
                     "D3", "E3", "F3", "D3", "E3", "C3", "D3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["1"] * 44 + ["4"], ["4"] * 12],
          "answers": [True] * 45,
          "name": "fig60",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)
    return all_ex


def fetch_two_voice_species4():
    all_ex = []
    # fig 61
    ex = {"notes": [["R", "C4", "A3", "D4", "B3", "E4"],
                    ["C3", "F3", "D3", "G3", "E3"]],
          "durations": [["2"] + ["4"] * 4 + ["2"], ["4"] * 5],
          # First false due to mode estimation failure in partial sequences
          "answers": [False] + [True] * 9, # 10 total ???
          "name": "fig61",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 62
    ex = {"notes": [["R", "E4", "D4", "C4", "B3", "C4"],
                    ["C3", "F3", "E3", "D3", "C3"]],
          "durations": [["2"] + ["4"] * 3 + ["2"] +["4"], ["4"] * 5],
          "answers": [True] * 9,
          "name": "fig62",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 63
    ex = {"notes": [["R", "G3", "F3", "E3", "D3"],
                    ["E3", "D3", "C3", "B2"]],
          "durations": [["2"] + ["4"] * 3 + ["2"], ["4"] * 4],
          # Handle mode estimation error for partial sequence
          "answers": [False] + [True] * 7,
          "name": "fig63",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 73
    ex = {"notes": [["R", "A3", "D4", "C4", "Bb3", "G3", "A3", "C4", "F4", "E4", "D4", "C#4", "D4"],
                    ["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"]],
          "durations": [["2"] + ["4"] * 4 + ["2"] * 2 + ["4"] * 4 + ["2"] + ["4"],
                        ["4"] * 11],
          "answers": [True] * 21,
          "name": "fig73",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 74
    ex = {"notes": [["D3", "F3", "E3", "D3", "G3", "F3", "A3", "G3", "F3", "E3", "D3"],
                    ["R", "D2", "D3", "C3", "B2", "E3", "D3", "F3", "E3", "D3", "C#3", "D3"]],
          "durations": [["4"] * 11,
                        ["2"] + ["4"] * 9 + ["2"] + ["4"]],
          "answers": [True] * 21,
          "name": "fig74",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 75
    ex = {"notes": [["R", "E4", "C4", "B3", "C4", "E3", "F3", "C4", "B3", "E4", "D4", "E4"],
                    ["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"]],
          "durations": [["2"] + ["4"] * 2 + ["2"] * 2 + ["4"] * 5 + ["2"] + ["4"],
                        ["4"] * 10],
          "answers": [True] * 19,
          "name": "fig75",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 76
    ex = {"notes": [["E3", "C3", "D3", "C3", "A2", "A3", "G3", "E3", "F3", "E3"],
                    ["R", "E2", "A2", "G2", "F2", "D2", "D3", "C3", "E3", "D3", "E3"]],
          "durations": [["4"] * 10,
                        ["2"] + ["4"] * 8 + ["2"] + ["4"]],
          "answers": [True] * 19,
          "name": "fig76",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)

    # fig 77
    ex = {"notes": [["R", "F3", "E3", "C3", "F3", "A3", "G3", "F3", "E3", "A3", "F3", "E3", "F3"],
                    ["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"]],
          "durations": [["2"] + ["4"] * 10 + ["2"] + ["4"],
                        ["4"] * 12],
          "answers": [True] * 23,
          "name": "fig77",
          "cantus_firmus_voice": 1}
    all_ex.append(ex)

    # fig 78
    ex = {"notes": [["F2", "G2", "A2", "F2", "D2", "E2", "F2", "C3", "A2", "F2", "G2", "F2"],
                    ["R", "F2", "E2", "D2", "Bb1", "G1", "G2", "F2", "E2", "D2", "F2", "E2", "F2"]],
          "durations": [["4"] * 12,
                        ["2"] + ["4"] * 10 + ["2"] + ["4"]],
          "answers": [True] * 23,
          "name": "fig78",
          "cantus_firmus_voice": 0}
    all_ex.append(ex)
    return all_ex
