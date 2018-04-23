# Author: Kyle Kastner
# License: BSD 3-Clause
# http://mcts.ai/pubs/mcts-survey-master.pdf
# See similar implementation here
# https://github.com/junxiaosong/AlphaZero_Gomoku

# changes from high level pseudo-code in survey
# expand all children, but only rollout one
# section biases to unexplored nodes, so the children with no rollout
# will be explored quickly

import numpy as np
import copy
from dataset_wrap import two_voice_species1_wrap
from analysis import analyze_two_voices
from shared_mcts import MCTS

all_l, l_map, p_map, all_i = two_voice_species1_wrap()
l_inv_map = {v: k for k, v in l_map.items()}
p_inv_map = {v: k for k, v in p_map.items()}

va_p = [p_map[k] for k in sorted(p_map.keys())]
j_map = {p_inv_map[k1]: k1 for k1 in va_p}
j_map = {k: v for k, v in j_map.items() if k > 0}
j_inv_map = {v: k for k, v in j_map.items()}

j_acts_map = {k: v for k, v in enumerate(sorted(j_map.keys()))}
j_acts_inv_map = {v: k for k, v in j_acts_map.items()}

class TwoVoiceSpecies1Manager(object):
    def __init__(self, guide_index, default_mode="C", offset_value=60, tonality="-", rollout_limit=1000):
        self.default_mode = default_mode
        self.offset_value = offset_value
        # M or m or - major or minor or any tonality
        self.tonality = tonality
        self.guide_trace = all_l[guide_index]

        self.random_state = np.random.RandomState(1999)
        self.rollout_limit = rollout_limit

    def get_next_state(self, state, action):
        act = j_acts_map[action]
        new_state = [state[0] + [act], state[1]]
        return new_state

    def get_action_space(self):
        return list(range(len(j_acts_map.keys())))

    def get_valid_actions(self, state):
        s0 = np.array(state[0])
        s1 = np.array(state[1])

        if self.tonality == "M":
            # disallow minor 3rds and 6ths
            disallowed = [3, 8, 15, 20, 27]
        elif self.tonality == "m":
            # disallow major 3rds and 6ths
            disallowed = [4, 9, 16, 21, 28]
        elif self.tonality == "-":
            disallowed = []
        else:
            raise ValueError("self.tonality setting {} not understood".format(self.tonality))

        if len(state[0]) == 0:
            # for first notes, keep it pretty open
            va_p = [p_map[k] for k in sorted(p_map.keys())]
            acts_i = [p for p in va_p]
            acts = [p_inv_map[a] for a in acts_i]

            # no voice crossing, m/M2
            acts = [a for a in acts if a > 2]

            # remove combinations violating tonality
            acts = [a for a in acts if a not in disallowed]

            acts_r = [j_acts_inv_map[a] for a in acts if a in j_acts_inv_map]
            return acts_r
        else:
            va_p = [p_map[k] for k in sorted(p_map.keys())]
            acts_i = [p for p in va_p]
            acts = [p_inv_map[a] for a in acts_i]

            # no leaps of greater than a 4th
            acts = [a for a in acts if abs(a - state[0][-1]) <= 5]

            # no voice crossing, m/M2
            acts = [a for a in acts if a > 2]

            # remove combinations violating tonality
            acts = [a for a in acts if a not in disallowed]

            acts_r = [j_acts_inv_map[a] for a in acts if a in j_acts_inv_map]
            return acts_r

    def get_init_state(self):
        # need to inspect the others...
        top = []
        bot = self.guide_trace
        return copy.deepcopy([top, bot])

    def _rollout_fn(self, state):
        return self.random_state.choice(self.get_valid_actions(state))

    def _score(self, state):
        s0 = np.array(state[0])
        s1 = np.array(state[1])
        bot = s1 + self.offset_value
        top = bot[:len(s0)] + s0
        unique_count = len(set(list(s0))) / float(len(s0))
        smooth_s = 1. / np.sum(np.abs(np.diff(top)))
        unique_max = 1. / float(len(np.where(top == np.max(top))[0]))
        return smooth_s #+ unique_max + unique_count

    def rollout_from_state(self, state):
        s = state
        w, sc, e = self.is_finished(state)
        if e:
            if w == -1:
                return -1
            elif w == 0:
                return sc
            else:
                return self._score(s)

        c = 0
        while True:
            a = self._rollout_fn(s)
            s = self.get_next_state(s, a)
            w, sc, e = self.is_finished(s)
            c += 1
            if e:
                if w == -1:
                    return -1
                elif w == 0:
                    return sc
                else:
                    return self._score(s)

            if c > self.rollout_limit:
                return 0.

    def is_finished(self, state):
        if len(self.get_valid_actions(state)) == 0:
            return -1., -1., True

        if len(state[0]) == 0:
            # nothing has happened yet
            return 0, 0., False

        ns0 = state[0] + [0] * (len(state[1]) - len(state[0]))
        s_l = [ns0, state[1]]

        s = np.array(s_l)
        s[1, :] += self.offset_value
        s[0, :] += s[1, :]

        parts = s
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        # add caching here?
        aok = analyze_two_voices(parts, durations, key_signature, time_signature,
                                 species="species1_minimal", cantus_firmus_voices=[1])

        if len(aok[1]["False"]) > 0:
            first_error = aok[1]["False"][0]
        else:
            first_error = np.inf

        if len(state[0]) < len(state[1]):
            # error is out of our control (in the padded notes)
            if first_error > (len(state[0]) - 1):
                return 0, 0., False
            else:
                # made a mistake
                return 0, -1. + len(state[0]) / float(len(state[1])), True
        elif aok[0]:
            return 1, 1., True
        else:
            return -1, -1., True


if __name__ == "__main__":
    import time
    from visualization import pitches_and_durations_to_pretty_midi
    from visualization import plot_pitches_and_durations
    from analysis import fixup_parts_durations
    from analysis import intervals_from_midi

    all_parts = []
    all_durations = []
    mcts_random = np.random.RandomState(1110)
    for guide_idx in range(len(all_l)):
        tvsp1m = TwoVoiceSpecies1Manager(guide_idx)
        mcts = MCTS(tvsp1m, n_playout=1000, random_state=mcts_random)
        resets = 0
        n_valid_samples = 0
        valid_state_traces = []
        temp = 1.
        noise = True
        while True:
            if n_valid_samples >= 1:
                print("Got a valid sample")
                break
            resets += 1
            if resets > 30:
                temp = 1E-3
                noise = False
            state = mcts.state_manager.get_init_state()
            winner, score, end = mcts.state_manager.is_finished(state)
            states = [state]
            while True:
                if not end:
                    print("guide {}, step {}, resets {}".format(guide_idx, len(states), resets))
                    #print(state)
                    #a, ap = mcts.sample_action(state, temp=temp, add_noise=noise)
                    a, ap = mcts.get_action(state)

                    if a is None:
                        print("Ran out of valid actions, stopping early at step {}".format(len(states)))
                        valid_state_traces.append(states[-1])
                        n_valid_samples += 1
                        break

                    for i in mcts.root.children_.keys():
                        print(i, mcts.root.children_[i].__dict__)
                        print("")
                    print(state)
                    mcts.update_tree_root(a)
                    state = mcts.state_manager.get_next_state(state, a)
                    states.append(state)
                    winner, score, end = mcts.state_manager.is_finished(state)
                else:
                    mcts.reconstruct_tree()
                    print(state)
                    if len(states) > 1 and len(states[-1][0]) == len(states[-1][1]):
                        print("Got to the end")
                        n_valid_samples += 1
                        valid_state_traces.append(states[-1])
                        break
                    else:
                        print("Finished in {} steps".format(len(states)))
                        break

        s = valid_state_traces[0]
        s0 = np.array(s[0])
        s1 = np.array(s[1])
        bot = s1 + mcts.state_manager.offset_value
        bot = bot[:len(s0)]
        top = bot + s0
        parts = [list(top), list(bot)]
        durations = [['4'] * len(p) for p in parts]
        durations = [[int(di) for di in d] for d in durations]
        interval_figures = intervals_from_midi(parts, durations)
        _, interval_durations = fixup_parts_durations(parts, durations)
        all_parts.append(parts)
        all_durations.append(durations)
        print("completed {}".format(guide_idx))

    # now dump samples
    pitches_and_durations_to_pretty_midi(all_parts, all_durations,
                                         save_dir="two_voice_puct_mcts_samples",
                                         name_tag="two_voice_puct_mcts_sample_{}.mid",
                                         default_quarter_length=240,
                                         voice_params="piano")
    key_signature = "C"
    time_signature = "4/4"
    clefs = ["treble", "bass"]
    plot_pitches_and_durations(all_parts, all_durations,
                               save_dir="two_voice_puct_mcts_plots",
                               name_tag="two_voice_puct_mcts_plot_{}.ly")
                               #interval_figures=interval_figures,
                               #interval_durations=interval_durations,
                               #use_clefs=clefs)

    # add caching here?
    # minimal check during rollout
    from IPython import embed; embed(); raise ValueError()
