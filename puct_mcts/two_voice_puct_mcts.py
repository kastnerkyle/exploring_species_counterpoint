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


def softmax(x):
    assert len(x.shape) == 1
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class TreeNode(object):
    def __init__(self, prior_prob, parent):
        self.parent = parent
        self.Q_ = 0.
        self.P_ = float(prior_prob)
        # action -> tree node
        self.children_ = {}
        self.n_visits_ = 0

    def expand(self, actions_and_probs):
        for action, prob in actions_and_probs:
            if action not in self.children_:
                self.children_[action] = TreeNode(prob, self)

    def is_leaf(self):
        return self.children_ == {}

    def is_root(self):
        return self.parent is None

    def _update(self, value):
        self.n_visits_ += 1
        # not tracking W directly
        # original update is
        # n_visits += 1
        # W += v
        # Q = W / n_visits
        # so,
        # the old W = Q * (n_visits - 1)
        # new W = old W + v
        # new Q = new W / n_visits
        # plugging in new W
        # new Q = (old W + v) / n_visits
        # plugging in old W
        # new Q = (Q * (n_visits - 1) + v)/n_visits
        # new_Q = (Q * n_visits - Q + v)/n_visits
        # new_Q = Q * n_visits/n_visits - Q/n_visits + v/n_visits
        # new_Q = Q - Q/n_visits + v/n_visits
        # new_Q = Q + (v - Q) / n_visits
        # new_Q += (v - Q) / n_visits
        self.Q_ += (value - self.Q_) / float(self.n_visits_)

    def update(self, value):
        if self.parent != None:
            # negative in the original code due to being the opposing player
            self.parent.update(value)
        self._update(value)

    def get_value(self, c_puct):
        self.U_ = c_puct * self.P_ * np.sqrt(float(self.parent.n_visits_)) / float(1. + self.n_visits_)
        return self.Q_ + self.U_

    def get_best(self, c_puct):
        best = max(self.children_.iteritems(), key=lambda x: x[1].get_value(c_puct))
        return best


class MCTS(object):
    def __init__(self, state_manager, c_puct=1.4, n_playout=1000, random_state=None):
        if random_state is None:
            raise ValueError("Must pass random_state object")
        self.random_state = random_state
        self.root = TreeNode(1., None)
        # state manager must, itself have *NO* state / updating behavior
        # internally. Otherwise we need deepcopy() in get_move_probs
        self.state_manager = state_manager
        self.c_puct = c_puct
        self.n_playout = n_playout
        self.tree_subs_ = []
        self.warn_at_ = 10000

    def playout(self, state):
        node = self.root
        while True:
            if node.is_leaf():
                break
            action, node = node.get_best(self.c_puct)
            state = self.state_manager.get_next_state(state, action)
        winner, score, end = self.state_manager.is_finished(state)
        if not end:
            # uniform prior probs
            actions = self.state_manager.get_valid_actions(state)
            action_space = self.state_manager.get_action_space()
            probs = np.ones((len(actions))) / float(len(actions))
            actions_and_probs = list(zip(actions, probs))
            node.expand(actions_and_probs)
        value = self.state_manager.rollout_from_state(state)
        node.update(value)
        return None

    def get_action_probs(self, state, temp=1E-3):
        # low temp -> nearly argmax
        for n in range(self.n_playout):
            self.playout(state)

        act_visits = [(act, node.n_visits_) for act, node in self.root.children_.items()]
        if len(act_visits) == 0:
            return None, None
        actions, visits = zip(*act_visits)
        action_probs = softmax(1. / temp * np.log(visits))
        return actions, action_probs

    def sample_action(self, state, temp=1E-3, add_noise=True,
                      dirichlet_coeff1=0.25, dirichlet_coeff2=0.3):
        vsz = len(self.state_manager.get_action_space())
        act_probs = np.zeros((vsz,))
        acts, probs = self.get_action_probs(state, temp)
        if acts == None:
            return acts, probs
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
        if acts == None:
            return acts, probs
        act_probs[list(acts)] = probs
        maxes = np.max(act_probs)
        opts = np.where(act_probs == maxes)[0]
        if len(opts) > 1:
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
        self.root = TreeNode(1., None)
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
