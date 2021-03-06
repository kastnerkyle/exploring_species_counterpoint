# Author: Kyle Kastner
# License: BSD 3-Clause
# http://mcts.ai/pubs/mcts-survey-master.pdf
# https://github.com/junxiaosong/AlphaZero_Gomoku

# Key modifications from base MCTS described in survey paper
# use PUCT instead of base UCT
# Expand() expands *all* children, but only does rollout on 1 of them
# Selection will naturally bias toward the unexplored nodes
# so the "fresh" children will quickly be explored
# This is to closer match AlphaGo Zero, see appendix of the Nature paper

import numpy as np
from common_mcts import TreeNode
import copy


def softmax(x):
    assert len(x.shape) == 1
    probs = np.exp(x - np.max(x))
    probs /= np.sum(probs)
    return probs


class NetMCTS(object):
    def __init__(self, policy_value_fn, state_manager, c_puct=1.4, n_playout=1000, random_state=None):
        if random_state is None:
            raise ValueError("Must pass random_state object")
        self.policy_fn = policy_value_fn
        self.root = TreeNode(None, 1.)
        self.c_puct = c_puct
        self.n_playout = n_playout
        # checks validity / end conditions
        # gives next_state
        # can also give valid_actions
        self.state_manager = state_manager
        self.random_state = random_state

    def make_full_sequence(self, partial_state_seq):
        # Hack to end on octave, since unison currently disallowed
        min_dist = np.inf
        min_poss = None
        last_state = partial_state_seq[-1]
        for poss in [-8, 8, 16]:
            dist = abs(poss - self.state_manager.original_inv_map[last_state[0]])
            if dist < min_dist:
                min_poss = poss
                min_dist = dist
        # map from "real space" to policy space
        final_move = self.state_manager.valid_action_inv_remapper[self.state_manager.valid_action_map[min_poss]]
        # add a bunch of eos for guide trace
        last_l = self.state_manager.guide_map[100]
        estate = np.array([final_move, last_l, last_l, last_l])
        full_seq = list(partial_state_seq) + [estate]
        return full_seq

    def playout(self, state):
        node = self.root
        states = []
        while True:
            if node.is_leaf():
                winner, end = self.state_manager.finished(state)
                if not end:
                    actions_and_probs, value = self.policy_fn(state)
                    # make this part "env aware"? check actions?
                    node.expand(actions_and_probs)
                if end:
                    full_seq = self.make_full_sequence(list(states))
                    midi = self.state_manager.reconstruct_sequence(full_seq)
                    local_musical_check = self.state_manager.evaluate_sequence(midi, minimal=True)

                    if local_musical_check[0]:
                        value = 1.
                    else:
                        value = -1.
                node.update(value)
                return value
            else:
                # greedy select
                action, node = node.get_best(self.c_puct)
                state = self.state_manager.next_state(state, action)
                states.append(state)

    def get_move_probs(self, state, temp=1E-3):
        mgr = copy.deepcopy(self.state_manager)
        for n in range(self.n_playout):
            self.playout(state)
            self.state_manager = copy.deepcopy(mgr)

        act_visits = [(act, node.n_visits_) for act, node in self.root.children_.items()]
        acts, visits = zip(*act_visits)
        act_probs = softmax(1. / temp * np.log(visits))
        return acts, act_probs

    def get_action(self, state, temp=1E-3, add_noise=True, dirichlet_coeff1=0.25, dirichlet_coeff2=0.3):
        vsz = len(self.state_manager.valid_actions(state))
        move_probs = np.zeros((vsz,))
        acts, probs = self.get_move_probs(state, temp)
        move_probs[list(acts)] = probs
        if add_noise:
            move = self.random_state.choice(acts, p=(1. - dirichlet_coeff1) * probs + dirichlet_coeff1 * self.random_state.dirichlet(dirichlet_coeff2 * np.ones(len(probs))))
        else:
            move = random_state.choice(acts, p=probs)
        return move, move_probs

    def update_to_move(self, move):
        # keep previous info, descend down the tree
        if move in self.root.children_:
            self.root = self.root.children_[move]
            self.root.parent = None
        else:
            print("Move argument {} to update_to_move not in actions {}, resetting".format(move, self.root.children_.keys()))
            self.root = TreeNode(None, 1.0)
