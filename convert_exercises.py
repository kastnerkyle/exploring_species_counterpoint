import os

with open("exercises.py", 'rb') as f:
    lines = f.readlines()

with open("new_exercises.py", 'wb') as f:
    line_counter = 0
    while line_counter < len(lines):
        l = lines[line_counter]
        if 'ex = {"notes"' not in l:
            f.write(l)
            line_counter += 1
        else:
            notes_lines = [l]
            duration_lines = []
            line_counter += 1
            mode = "notes"
            while True:
                ln = lines[line_counter]
                if mode == 'durations' and 'answers' in ln:
                    break
                elif 'durations' in ln or mode == 'durations':
                    mode = "durations"
                    duration_lines.append(ln)
                    line_counter += 1
                elif mode == 'notes' and 'answers' not in ln:
                    notes_lines.append(ln)
                    line_counter += 1
            """
            # to just rewrite as is, we do this...
            for nl in notes_lines:
                f.write(nl)
            for dl in duration_lines:
                f.write(dl)
            """
            # create a partial dict...
            duration_lines[-1] = duration_lines[-1][:-2] + "}"
            orig_start_part = notes_lines[0].split('"notes"')[0]
            notes_lines[0] = notes_lines[0].replace(" ", "")[3:]
            fc = "".join(notes_lines + duration_lines).replace(" ", "")
            try:
                sub_dict = eval(fc)
            except:
                from IPython import embed; embed(); raise ValueError()

            n = sub_dict["notes"]
            d = sub_dict["durations"]
            assert len(n) == len(d)
            comb = []
            for i in range(len(n)):
                assert len(n[i]) == len(d[i])
                comb.append(list(zip(n[i], d[i])))
            out_str = orig_start_part + '"notes_and_durations": {}'.format(comb) + ",\n"
            f.write(out_str)
