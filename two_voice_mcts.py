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

window_p, window_l, p_map, l_map, all_p, all_l, all_i = two_voice_species1_wrap()
p_inv_map = {v: k for k, v in p_map.items()}
# get rid of the awkward one?
all_l = [l for l in all_l if l[1] == 0]

class TwoVoiceSpecies1Manager(object):
    def __init__(self, guide_index, default_mode="C", rollout_limit=1000):
        self.default_mode = "C"
        self.offset_value = 60
        self.guide_trace = all_l[guide_index][1:-1]

        self.random_state = np.random.RandomState(1999)
        self.rollout_limit = rollout_limit

    def get_next_state(self, state, action):
        interval = p_inv_map[action]
        return [state[0] + [interval], state[1]]

    def get_action_space(self):
        return list(range(len({p for p in p_map if p < 97})))

    def get_valid_actions(self, state):
        if len(state[0]) > 0:
            s0 = np.array(state[0])
            s1 = np.array(state[1])
            # only allow actions within a jump of a 4th (5)
            # only allow harmonizations above - no voice crossing
            if len(state[0]) >= (len(state[1]) - 2):
                # allow unison on the last notes
                va = [p_map[k] for k in sorted(p_map.keys()) if abs(k - state[0][-1]) <= 5 and k >= 0]
            else:
                va = [p_map[k] for k in sorted(p_map.keys()) if abs(k - state[0][-1]) <= 5 and k > 0]

            # extra contingencies
            # disallow M3/m3 confusions
            # disallow m6/M6 confusions
            # disallow same on 15/16 (m3/M3)
            disallowed = []
            if 3 in s0:
                disallowed.append(4)
                disallowed.append(16)
            if 4 in s0:
                disallowed.append(3)
                disallowed.append(15)

            if 15 in s0:
                disallowed.append(4)
                disallowed.append(16)
            if 16 in s0:
                disallowed.append(3)
                disallowed.append(15)

            if 8 in s0:
                disallowed.append(9)
            if 9 in s0:
                disallowed.append(8)
            disallowed_actions = [p_map[d] for d in disallowed]

            va = [vai for vai in va if vai not in disallowed_actions]
            if len(va) == 0:
                print("Edge case, 0 valid actions...")
                from IPython import embed; embed(); raise ValueError()
            return va
        else:
            # could constrain the start much more, but leave it for now
            return [p_map[k] for k in sorted(p_map.keys()) if k < 97 and k >= 0]

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
        # smoothness score
        # range score
        # note diversity
        # interval diversity
        # distance from center of max note
        # distance from center of max interval
        # whether the peak is a unique note or repeated
        smooth_s = 1. / np.sum(np.abs(np.diff(top)))
        range_s = 1. / float(np.max([np.max(top) - np.min(top), 12]))
        note_p = -1. / len(set(top))
        interval_p = -1./ len(set(s0))
        farthest_from_center_interval = np.where(s0 == np.max(s0))[0]
        fci = np.argmax(np.abs(farthest_from_center_interval - len(s1) / 2.))
        fci_argmax = farthest_from_center_interval[fci]

        farthest_from_center_note = np.where(top == np.max(top))[0]
        fcn = np.argmax(np.abs(farthest_from_center_note - len(s1) / 2.))
        fcn_argmax = farthest_from_center_note[fcn]

        center_note_s = 1. if abs(len(s1) / 2. - fcn) < 3 else 0.
        center_interval_s = 1. if abs(len(s1) / 2. - fci) < 3 else 0.
        unique_peak = 1. if len(np.where(top == np.max(top))[0]) == 1 and center_note_s > 0 else 0.
        return smooth_s + range_s + note_p + interval_p + center_interval_s + center_note_s + unique_peak

    def rollout_from_state(self, state):
        s = state
        w, e = self.is_finished(state)
        if e:
            if w == -1:
                return 0.
            elif w == 0:
                return -1
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
                    return -1
                else:
                    return self._score(s)

            if c > self.rollout_limit:
                return 0.

    def is_finished(self, state):
        orig_len = len(state[0])
        if orig_len == 0:
            # nothing has happened yet
            return -1, False

        # do quick hand check for key start to speed it up
        if state[0][0] not in [0, 12]:
            return 0, True

        # if the only thing so far is the first note, and we passed that check
        # it's incomplete
        if orig_len == 1:
            return -1, False

        # if its at the end, finish on an octave fifth or unison
        if orig_len == len(state[1]):
            if state[0][-1] not in [0, 12]:
                return 0, True

        ns0 = state[0] + [0] * (len(state[1]) - orig_len)
        # the state to check
        s = [ns0, state[1]]

        s = np.array(s)
        s[1, :] += self.offset_value
        s[0, :] += s[1, :]

        parts = s
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        # add caching here?
        # minimal check during rollout
        aok = analyze_two_voices(parts, durations, key_signature, time_signature,
                                 species="species1_minimal", cantus_firmus_voices=[1])
        if len(aok[1]["False"]) > 0:
            first_error = aok[1]["False"][0]
        else:
            first_error = np.inf

        if orig_len < len(state[1]):
            # error is out of our control (in the padded notes)
            if first_error > (orig_len - 1):
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
            winner, end = mcts.state_manager.is_finished(state)
            states = [state]
            while True:
                if not end:
                    print("guide {}, step {}, resets {}".format(guide_idx, len(states), resets))
                    #print(state)
                    #a, ap = mcts.sample_action(state, temp=temp, add_noise=noise)
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
        top = bot + s0
        parts = [list(top), list(bot)]
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
    plot_pitches_and_durations(all_parts, all_durations,
                               save_dir="mcts_plots",
                               name_tag="mcts_plot_{}.ly")
                               #interval_figures=interval_figures,
                               #interval_durations=interval_durations,
                               #use_clefs=clefs)

    # now dump samples
    pitches_and_durations_to_pretty_midi(all_parts, all_durations,
                                         save_dir="mcts_samples",
                                         name_tag="mcts_sample_{}.mid",
                                         default_quarter_length=240,
                                         voice_params="piano")
    # add caching here?
    # minimal check during rollout
    from IPython import embed; embed(); raise ValueError()
