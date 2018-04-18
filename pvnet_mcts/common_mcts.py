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

class TreeNode(object):
    def __init__(self, parent, prior_prob):
        self.parent = parent
        self.Q_ = 0
        self.P = prior_prob
        # action -> tree node
        self.children_ = {}
        self.n_visits_ = 0

    def expand(self, actions_and_probs):
        for action, prob in actions_and_probs:
            if action not in self.children_:
                self.children_[action] = TreeNode(self, prob)

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
            # negative in the original code due to being the opposing player?
            #self.parent.update(-value)
            self.parent.update(value)
        self._update(value)

    def get_value(self, c_puct):
        U = c_puct * self.P * np.sqrt(self.parent.n_visits_) / (self.n_visits_ + 1)
        return self.Q_ + U

    def get_best(self, c_puct):
        best = max(self.children_.iteritems(), key=lambda x: x[1].get_value(c_puct))
        return best
