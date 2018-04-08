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

# simple state machine, counting
class StateManager(object):
    def __init__(self):
        pass

    def next_state(self, state, action):
        if action == state:
            # if you choose action == state, progress, else stuck
            return state + 1
        else:
            return 0

    def valid_actions(self, state):
        return tuple(range(5))

    def finished(self, state):
        if state == 4:
            return 1, True
        else:
            return 0, False


random_state = np.random.RandomState(11)
state_mgr = StateManager()

def random_policy_fn(state):
    actions = state_mgr.valid_actions(state)
    action_probs = random_state.rand(len(actions))
    action_probs = action_probs / np.sum(action_probs)
    return tuple(zip(actions, action_probs))


def policy_value_fn(state):
    actions = state_mgr.valid_actions(state)
    action_probs = np.ones(len(actions)) / float(len(actions))
    comb = tuple(zip(actions, action_probs))
    return comb, 0


class MCTS(object):
    def __init__(self, policy_value_fn, rollout_policy_fn, c_puct=1, n_playout=100):
        self.policy_fn = policy_value_fn
        self.rollout_policy_fn = rollout_policy_fn
        self.root = TreeNode(None, 1.)
        self.c_puct = c_puct
        self.n_playout = n_playout

    def playout(self, state):
        node = self.root
        while True:
            if node.is_leaf():
                winner, end = state_mgr.finished(state)
                if not end:
                    actions_and_probs, _ = self.policy_fn(state)
                    node.expand(actions_and_probs)
                value = self.evaluate(state)
                # negative in the original code due to being the opposing player?
                #node.update(-value)
                node.update(value)
                return value
            else:
                # greedy select
                action, node = node.get_best(self.c_puct)
                state = state_mgr.next_state(state, action)

    def evaluate(self, state, limit=1600):
        orig_state = state
        states_trace = [state]
        for i in range(limit):
            winner, end = state_mgr.finished(state)
            if end:
                break
            actions_and_probs = self.rollout_policy_fn(state)
            max_action = max(actions_and_probs, key=lambda x: x[1])[0]
            state = state_mgr.next_state(state, max_action)
            states_trace.append(state)
        else:
            print("Evaluate hit maximum step limit {} without termination state".format(limit))

        # custom win evaluation here for shortest path
        if winner == 1:
            return 1. / len(states_trace)
        else:
            return 0

    def get_best_action(self, state):
        for n in range(self.n_playout):
            self.playout(state)
        # should visit most valuable one the most often
        return max(self.root.children_.iteritems(), key=lambda x: x[1].n_visits_)[0]

    def update_to_move(self, move):
        # keep previous info
        if move in self.root.children_:
            self.root = self.root.children_[move]
            self.root.parent = None
        else:
            print("Move argument {} to update_to_move not in actions {}, resetting".format(move, self.root.children_.keys()))
            self.root = TreeNode(None, 1.0)
