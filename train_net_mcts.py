from net_mcts import NetMCTS
import numpy as np

# simple state machine, counting
class MusicStateManager(object):
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

state_mgr = MusicStateManager()
random_state = np.random.RandomState(11)

def dummy_pv(state):
    # this should wrap a nn
    return zip(list(range(5)), np.ones((5,)) / 5.), 1

state = 0
mcts = NetMCTS(dummy_pv, state_mgr, random_state=random_state)
move = mcts.get_action(state)
mcts.update_to_move(move)
from IPython import embed; embed(); raise ValueError()
