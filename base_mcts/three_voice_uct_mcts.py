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
from shared_mcts import MCTS
from dataset_wrap import three_voice_species1_wrap
from analysis import analyze_three_voices

all_l, all_c_set, u_map, m_map, um_map, l_map, all_i = three_voice_species1_wrap()
u_inv_map = {v: k for k, v in u_map.items()}
m_inv_map = {v: k for k, v in m_map.items()}
um_inv_map = {v: k for k, v in um_map.items()}
l_inv_map = {v: k for k, v in l_map.items()}

va_u = [u_map[k] for k in sorted(u_map.keys())]
va_m = [m_map[k] for k in sorted(m_map.keys())]
combs = [(u, m) for u in va_u for m in va_m]
j_map = {(u_inv_map[k1], m_inv_map[k2]): (k1, k2) for k1, k2 in combs}
j_map = {k: v for k, v in j_map.items() if k[0] >= k[1]}
j_map = {k: v for k, v in j_map.items() if k[0] != 0 and k[1] != 0}

#j_map = {(k1, k2): (u_map[k1], m_map[k2]) for k1 in sorted(u_map.keys()) for k2 in sorted(m_map.keys())}
# don't constrain to only groupings found in the dataset
#j_map = {k: v for k, v in j_map.items() if k in all_c_set}

j_inv_map = {v: k for k, v in j_map.items()}
j_acts_map = {k: v for k, v in enumerate(sorted(j_map.keys()))}
j_acts_inv_map = {v: k for k, v in j_acts_map.items()}

class ThreeVoiceSpecies1Manager(object):
    def __init__(self, guide_index, default_mode="C", offset_value=48, tonality="M", rollout_limit=1000):
        self.default_mode = default_mode
        self.offset_value = offset_value
        # M or m or - major or minor or any tonality
        self.tonality = tonality
        self.guide_trace = all_l[guide_index]

        self.random_state = np.random.RandomState(1999)
        self.rollout_limit = rollout_limit

    def get_next_state(self, state, action):
        tup_act = j_acts_map[action]
        new_state = [state[0] + [tup_act[0]], state[1] + [tup_act[1]], state[2]]
        return new_state

    def get_action_space(self):
        return list(range(len(j_acts_map.keys())))

    def get_valid_actions(self, state):
        s0 = np.array(state[0])
        s1 = np.array(state[1])
        s2 = np.array(state[2])

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
            va_u = [u_map[k] for k in sorted(u_map.keys())]
            va_m = [m_map[k] for k in sorted(m_map.keys())]
            combs = [(u, m) for u in va_u for m in va_m]
            combs = [(u_inv_map[c[0]], m_inv_map[c[1]]) for c in combs]

            # no voice crossing, m/M2 or unison
            combs = [c for c in combs if abs(c[1] - c[0]) > 2 and c[0] > c[1]]

            # remove combinations that violate our previous settings for m/M tonality
            combs = [c for c in combs
                     if (c[0] not in disallowed and c[1] not in disallowed)]

            # convert to correct option (intervals)
            # make sure it's a viable action
            comb_acts = [j_acts_inv_map[c] for c in combs if c in j_acts_inv_map]
            va = comb_acts
            return va
        else:
            va_u = [u_map[k] for k in sorted(u_map.keys())]
            va_m = [m_map[k] for k in sorted(m_map.keys())]
            combs = [(u, m) for u in va_u for m in va_m]
            combs = [(u_inv_map[c[0]], m_inv_map[c[1]]) for c in combs]
            # no leaps of greater than a 6th in either voice
            combs = [c for c in combs if abs(c[0] - state[0][-1]) <= 9]
            combs = [c for c in combs if abs(c[1] - state[1][-1]) <= 9]

            # heavily constrain top voice, no leap greater than a 4th
            combs = [c for c in combs if abs(c[0] - state[0][-1]) <= 5]

            # no voice crossing, m/M2 or unison
            combs = [c for c in combs if abs(c[1] - c[0]) > 2 and c[0] > c[1]]

            # remove combinations that violate our previous settings for m/M tonality
            combs = [c for c in combs
                     if (c[0] not in disallowed and c[1] not in disallowed)]
            # convert to correct option (intervals)
            # make sure it's a viable action
            comb_acts = [j_acts_inv_map[c] for c in combs if c in j_acts_inv_map]
            va = comb_acts
            return va

    def get_init_state(self):
        top = []
        mid = []
        bot = self.guide_trace
        return copy.deepcopy([top, mid, bot])

    def _rollout_fn(self, state):
        return self.random_state.choice(self.get_valid_actions(state))

    def _score(self, state):
        s0 = np.array(state[0])
        s1 = np.array(state[1])
        s2 = np.array(state[2])
        bot = s2 + self.offset_value
        mid = bot[:len(s1)] + s1
        top = bot[:len(s0)] + s0
        smooth_s0 = 1. / np.sum(np.abs(np.diff(top)))
        smooth_s1 = 1. / np.sum(np.abs(np.diff(mid)))
        unique_max = 1. / float(len(np.where(top == np.max(top))[0]))
        unique_count = 1. / float(len(set(s0)))
        return smooth_s0 #1. + 1. * smooth_s0 + .25 * smooth_s1 + .25 * unique_max

    def rollout_from_state(self, state):
        s = state
        w, sc, e = self.is_finished(state)
        if e:
            if w == -1:
                return -1.
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
        if len(state[0]) != len(state[1]):
            raise ValueError("Something bad in is_finished")

        if len(self.get_valid_actions(state)) == 0:
            return -1., -1., True

        if len(state[0]) == 0:
            # nothing happened yet
            return 0, 0., False

        ## only grade it at the end?
        #if len(state[0]) != len(state[2]):
        #    return -1, False

        ns0 = state[0] + [0] * (len(state[2]) - len(state[0]))
        ns1 = state[1] + [0] * (len(state[2]) - len(state[1]))
        # the state to check
        s_l = [ns0, ns1, state[2]]

        s = np.array(s_l)
        s[2, :] += self.offset_value
        s[0, :] += s[2, :]
        s[1, :] += s[2, :]

        parts = s
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        # minimal check during rollout
        aok = analyze_three_voices(parts, durations, key_signature, time_signature,
                                   species="species1_minimal", cantus_firmus_voices=[2])

        if len(aok[1]["False"]) > 0:
            first_error = aok[1]["False"][0]
        else:
            first_error = np.inf

        if len(state[0]) < len(state[2]):
            # error is out of our control (in the padded notes)
            if first_error > (len(state[0]) - 1):
                return 0, 0., False
            else:
                # made a mistake
                return 0, -1. + len(state[0]) / float(len(state[2])), True
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
        tvsp1m = ThreeVoiceSpecies1Manager(guide_idx)
        mcts = MCTS(tvsp1m, n_playout=1000, random_state=mcts_random)
        resets = 0
        n_valid_samples = 0
        valid_state_traces = []
        temp = 1.
        noise = True
        exact = True
        while True:
            if n_valid_samples >= 1:
                print("Got a valid sample")
                break
            resets += 1
            if resets > 10:
                temp = 1E-3
                noise = False
            elif resets > 15:
                exact = True
            state = mcts.state_manager.get_init_state()
            winner, score, end = mcts.state_manager.is_finished(state)
            states = [state]

            while True:
                if not end:
                    print("guide {}, step {}, resets {}".format(guide_idx, len(states), resets))
                    if not exact:
                        a, ap = mcts.sample_action(state, temp=temp, add_noise=noise)
                    else:
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
                    if len(states[-1][0]) < len(states[-1][2]) and end:
                        end = False
                else:
                    mcts.reconstruct_tree()
                    print(state)
                    if len(states) > 1 and len(states[-1][0]) == len(states[-1][2]):
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
        s2 = np.array(s[2])
        bot = s2 + mcts.state_manager.offset_value
        bot = bot[:len(s0)]
        mid = bot + s1
        top = bot + s0
        parts = [list(top), list(mid), list(bot)]
        durations = [['4'] * len(p) for p in parts]
        durations = [[int(di) for di in d] for d in durations]
        interval_figures = intervals_from_midi(parts, durations)
        _, interval_durations = fixup_parts_durations(parts, durations)
        all_parts.append(parts)
        all_durations.append(durations)
        print("completed {}".format(guide_idx))
    key_signature = "C"
    time_signature = "4/4"
    clefs = ["treble", "bass"]
    # now dump samples
    pitches_and_durations_to_pretty_midi(all_parts, all_durations,
                                         save_dir="three_voice_uct_mcts_samples",
                                         name_tag="three_voice_uct_mcts_sample_{}.mid",
                                         default_quarter_length=240,
                                         voice_params="piano")

    plot_pitches_and_durations(all_parts, all_durations,
                               save_dir="three_voice_uct_mcts_plots",
                               name_tag="three_voice_uct_mcts_plot_{}.ly")
                               #interval_figures=interval_figures,
                               #interval_durations=interval_durations,
                               #use_clefs=clefs)

    # add caching here?
    # minimal check during rollout
    from IPython import embed; embed(); raise ValueError()
