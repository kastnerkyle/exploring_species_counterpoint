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
from dataset_wrap import three_voice_species1_wrap
from analysis import analyze_three_voices

all_l, all_c_set, u_map, m_map, um_map, l_map, all_i = three_voice_species1_wrap()
u_inv_map = {v: k for k, v in u_map.items()}
m_inv_map = {v: k for k, v in m_map.items()}
um_inv_map = {v: k for k, v in um_map.items()}
l_inv_map = {v: k for k, v in l_map.items()}
j_map = {(k1, k2): (u_map[k1], m_map[k2]) for k1 in sorted(u_map.keys()) for k2 in sorted(m_map.keys())}
j_map = {k: v for k, v in j_map.items() if k[0] >= k[1]}
j_map = {k: v for k, v in j_map.items() if k[0] != 0 and k[1] != 0}
# don't constrain to only groupings found in the dataset
#j_map = {k: v for k, v in j_map.items() if k in all_c_set}

j_inv_map = {v: k for k, v in j_map.items()}
j_acts_map = {k: v for k, v in enumerate(sorted(j_map.keys()))}
j_acts_inv_map = {v: k for k, v in j_acts_map.items()}

class ThreeVoiceSpecies1Manager(object):
    def __init__(self, guide_index, default_mode="C", rollout_limit=1000):
        self.default_mode = "C"
        self.offset_value = 60
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

        mp = [3, 8, 15]
        Mp = [4, 9, 16]

        if len(state[0]) == 0:
            # for first note, keep it pretty open
            va_u = [u_map[k] for k in sorted(u_map.keys()) if k >= 0]
            va_m = [m_map[k] for k in sorted(m_map.keys()) if k >= 0]
            combs = [(u, m) for u in va_u for m in va_m]
            # disallow intervals too close together (no m/M2 clashes)
            combs = [c for c in combs if abs(c[0] - c[1]) > 2]
            # make sure it's a viable action
            comb_acts = [j_acts_inv_map[c] for c in combs if c in j_acts_inv_map]
            va = comb_acts
            return va
        else:
            # keep the jumps within a 4th on top voice
            va_u = [u_map[k] for k in sorted(u_map.keys()) if abs(k - state[0][-1]) <= 4 and k >= 0]
            va_m = [m_map[k] for k in sorted(m_map.keys()) if k >= 0]
            combs = [(u, m) for u in va_u for m in va_m]
            # disallow intervals too close together (no m/M2 clashes)
            combs = [c for c in combs if abs(c[0] - c[1]) > 2 and c[0] > c[1]]
            # check that it is an option
            comb_acts = [j_acts_inv_map[c] for c in combs if c in j_acts_inv_map]
            va = comb_acts
            if len(va) == 0:
                # no actions, allow leaps
                va_u = [u_map[k] for k in sorted(u_map.keys()) if k >= 0]
                va_m = [m_map[k] for k in sorted(m_map.keys()) if k >= 0]
                combs = [(u, m) for u in va_u for m in va_m]

                # avoid m2/M2 clases
                combs = [c for c in combs if abs(c[0] - c[1]) > 2]
                # make sure it is a valid action
                comb_acts = [j_acts_inv_map[c] for c in combs if c in j_acts_inv_map]
                if len(comb_acts) == 0:
                    print("Edge case, STILL no valid actions...")
                    from IPython import embed; embed(); raise ValueError()
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
        return 20. * smooth_s0 + smooth_s1 + 2. * unique_max

    def rollout_from_state(self, state):
        s = state
        w, e = self.is_finished(state)
        if e:
            if w == -1:
                return 0.
            elif w == 0:
                return -1.
            else:
                return self._score(s)

        c = 0
        while True:
            a = self._rollout_fn(s)
            s = self.get_next_state(s, a)
            w, e = self.is_finished(s)
            c += 1
            if e:
                if w == -1:
                    return 0.
                elif w == 0:
                    return -1.
                else:
                    return self._score(s)

            if c > self.rollout_limit:
                return 0.

    def is_finished(self, state):
        if len(state[0]) != len(state[1]):
            raise ValueError("Something bad in is_finished")

        if len(state[0]) == 0:
            # nothing happened yet
            return -1, False

        # only grade it at the end?
        if len(state[0]) != len(state[2]):
            return -1, False

        ns0 = state[0] + [0] * (len(state[2]) - len(state[0]))
        ns1 = state[1] + [0] * (len(state[2]) - len(state[1]))
        # the state to check
        s = [ns0, ns1, state[2]]

        s = np.array(s)
        s[2, :] += self.offset_value
        s[0, :] += s[2, :]
        s[1, :] += s[2, :]

        parts = s
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        # minimal check during rollout
        aok = analyze_three_voices(parts, durations, key_signature, time_signature,
                                   species="species1_minimal", cantus_firmus_voices=[1])

        if len(aok[1]["False"]) > 0:
            first_error = aok[1]["False"][0]
        else:
            first_error = np.inf

        if len(state[0]) < len(state[2]):
            # error is out of our control (in the padded notes)
            if first_error > (len(state[0]) - 1):
                return -1, False
            else:
                # made a mistake
                return 0, True

        """
        # mode estimation :|
        # should be species1
        aok_full = analyze_two_voices(parts, durations, key_signature, time_signature,
                                      species="species1_minimal", cantus_firmus_voices=[1])
        """
        aok_full = aok
        if aok_full[0]:
            return 1, True
        else:
            return 0, True

def softmax(x):
    assert len(x.shape) == 1
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class TreeNode(object):
    def __init__(self, parent):
        self.parent = parent
        self.W_ = 0
        # action -> tree node
        self.children_ = {}
        self.n_visits_ = 0

    def expand(self, actions_and_probs):
        for action, prob in actions_and_probs:
            if action not in self.children_:
                self.children_[action] = TreeNode(self)

    def is_leaf(self):
        return self.children_ == {}

    def is_root(self):
        return self.parent is None

    def _update(self, value):
        self.n_visits_ += 1
        self.W_ += value

    def update(self, value):
        if self.parent != None:
            # negative in the original code due to being the opposing player
            self.parent.update(value)
        self._update(value)

    def get_value(self, c_uct):
        if self.n_visits_ == 0:
            lp = 0.
        else:
            lp = self.W_ / float(self.n_visits_)

        if self.n_visits_ == 0:
            rp = np.inf
        else:
            rp = c_uct * np.sqrt(2 * np.log(self.parent.n_visits_) / float(self.n_visits_))
        return lp + rp

    def get_best(self, c_uct):
        best = max(self.children_.iteritems(), key=lambda x: x[1].get_value(c_uct))
        return best


class MCTS(object):
    def __init__(self, state_manager, c_uct=1.4, n_playout=1000, random_state=None):
        if random_state is None:
            raise ValueError("Must pass random_state object")
        self.random_state = random_state
        self.root = TreeNode(None)
        # state manager must, itself have *NO* state / updating behavior
        # internally. Otherwise we need deepcopy() in get_move_probs
        self.state_manager = state_manager
        self.c_uct = c_uct
        self.n_playout = n_playout
        self.tree_subs_ = []
        self.warn_at_ = 10000

    def playout(self, state):
        node = self.root
        while True:
            if node.is_leaf():
                break
            action, node = node.get_best(self.c_uct)
            state = self.state_manager.get_next_state(state, action)
        winner, end = self.state_manager.is_finished(state)
        if not end:
            # uniform prior probs
            actions = self.state_manager.get_valid_actions(state)
            action_space = self.state_manager.get_action_space()

            probs = np.zeros((len(action_space),))
            probs[actions] = np.ones((len(actions))) / float(len(actions))
            actions_and_probs = list(zip(actions, probs))

            node.expand(actions_and_probs)
        value = self.state_manager.rollout_from_state(state)
        # negative here
        node.update(value)
        return None

    def get_action_probs(self, state, temp=1E-3):
        # low temp -> nearly argmax
        for n in range(self.n_playout):
            self.playout(state)

        act_visits = [(act, node.n_visits_) for act, node in self.root.children_.items()]
        actions, visits = zip(*act_visits)
        action_probs = softmax(1. / temp * np.log(visits))
        return actions, action_probs

    def sample_action(self, state, temp=1E-3, add_noise=True,
                      dirichlet_coeff1=0.25, dirichlet_coeff2=0.3):
        vsz = len(self.state_manager.get_action_space())
        act_probs = np.zeros((vsz,))
        acts, probs = self.get_action_probs(state, temp)
        act_probs[list(acts)] = probs
        if add_noise:
            act = self.random_state.choice(acts, p=(1. - dirichlet_coeff1) * probs + dirichlet_coeff1 * self.random_state.dirichlet(dirichlet_coeff2 * np.ones(len(probs))))
        else:
            act = self.random_state.choice(acts, p=probs)
        return act, act_probs

    def get_action(self, state):
        vsz = len(self.state_manager.get_action_space())
        act_probs = np.zeros((vsz,))
        # temp doesn't matter for argmax
        acts, probs = self.get_action_probs(state, temp=1.)
        act_probs[list(acts)] = probs
        maxes = np.max(act_probs)
        opts = np.where(act_probs == maxes)[0]
        if len(opts) > 1:
            # choose the one with the highest win score if equal?
            # if 2 options are *exactly* equal, just choose 1 at random
            self.random_state.shuffle(opts)
        act = opts[0]
        return act, act_probs

    def update_tree_root(self, action):
        if action in self.root.children_:
            self.tree_subs_.append((self.root, self.root.children_[action]))
            if len(self.tree_subs_) > self.warn_at_:
                print("WARNING: Over {} tree_subs_ detected, watch memory".format(self.warn_at_))
                # only print the warning a few times
                self.warn_at_ = 10 * self.warn_at_
            self.root = self.root.children_[action]
            self.root.parent = None
        else:
            raise ValueError("Action argument {} neither in root.children_ {} and not == -1 (reset)".format(self.root.children_.keys()))

    def reconstruct_tree(self):
        # walk the list back to front, putting parents back in place
        # should reconstruct tree while still preserving counts...
        # this might be a bad idea for large state spaces
        for pair in self.tree_subs_[::-1]:
            self.root.parent = pair[0]
            self.root = pair[0]
        self.tree_subs_ = []

    def reset_tree(self):
        print("Resetting tree")
        self.root = TreeNode(None)
        self.tree_subs_ = []

if __name__ == "__main__":
    import time
    from visualization import pitches_and_durations_to_pretty_midi
    from visualization import plot_pitches_and_durations
    from analysis import fixup_parts_durations
    from analysis import intervals_from_midi

    all_parts = []
    all_durations = []
    mcts_random = np.random.RandomState(1110)
    #for guide_idx in [0]:
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
            winner, end = mcts.state_manager.is_finished(state)
            states = [state]

            while True:
                if not end:
                    print("guide {}, step {}, resets {}".format(guide_idx, len(states), resets))
                    #print(state)
                    if not exact:
                        a, ap = mcts.sample_action(state, temp=temp, add_noise=noise)
                    else:
                        a, ap = mcts.get_action(state)
                    for i in mcts.root.children_.keys():
                        print(i, mcts.root.children_[i].__dict__)
                        print("")
                    print(state)
                    mcts.update_tree_root(a)
                    state = mcts.state_manager.get_next_state(state, a)
                    states.append(state)
                    winner, end = mcts.state_manager.is_finished(state)
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
                                         save_dir="three_voice_mcts_samples",
                                         name_tag="three_voice_mcts_sample_{}.mid",
                                         default_quarter_length=240,
                                         voice_params="piano")

    plot_pitches_and_durations(all_parts, all_durations,
                               save_dir="three_voice_mcts_plots",
                               name_tag="three_voice_mcts_plot_{}.ly")
                               #interval_figures=interval_figures,
                               #interval_durations=interval_durations,
                               #use_clefs=clefs)

    # add caching here?
    # minimal check during rollout
    from IPython import embed; embed(); raise ValueError()