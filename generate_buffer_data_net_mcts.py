from net_mcts import NetMCTS
from networks import PolicyValueNetwork
from dataset_wrap import two_voice_species1_wrap
from analysis import analyze_two_voices
import numpy as np
import torch as th
from torch.autograd import Variable
import copy

window_p, window_l, p_map, l_map, all_p, all_l, all_i = two_voice_species1_wrap()

l_inv_map = {v: k for k, v in l_map.items()}
p_inv_map = {v: k for k, v in p_map.items()}

class MusicStateManager(object):
    def __init__(self, default_mode="C", random_state=None):
        if random_state is None:
            raise ValueError("Must pass random_state")
        self.random_state = random_state
        self.default_mode = default_mode
        # don't allow unison
        self.valid_action_map = {k: p_map[k] for k in sorted(p_map.keys()) if k < 97 and k != 0}
        # real movement to policy
        # policy action to real movement
        self.valid_action_inv_map = {v: k for k, v in self.valid_action_map.items()}
        self.valid_action_size = len(self.valid_action_map.keys())

        self.valid_action_remapper = {k: v for k, v in enumerate(sorted(self.valid_action_inv_map.keys()))}
        self.valid_action_inv_remapper = {v: k for k, v in self.valid_action_remapper.items()}

        # C3
        self.offset_value = 48
        self.current_ind_ = self.random_state.randint(len(all_l))
        self.current_guide_ = all_l[self.current_ind_]

        self.step_ = 0
        # 97 is default step state
        self.last_action_ = p_map[97]
        self.init_state_ = self.state_maker(self.step_)

    def state_maker(self, i):
        if i > (len(self.current_guide_) - 3):
            raise ValueError("i > guide")
        p = [self.last_action_]
        l = [l_map[g] for g in self.current_guide_[i:i + 3]]
        state = np.array(p + l)
        return state

    def next_state(self, state, action):
        self.last_action_ = action
        self.step_ += 1
        next_state = self.state_maker(self.step_)
        return next_state

    def reset(self, partial=False):
        if partial == False:
            self.current_ind_ = self.random_state.randint(len(all_l))
            self.current_guide_ = all_l[self.current_ind_]
        self.step_ = 0
        # 97 is default step state
        self.last_action_ = p_map[97]
        self.init_state_ = self.state_maker(self.step_)

    def valid_actions(self, state):
        # don't choose invalid actions...
        return tuple(range(self.valid_action_size))

    def finished(self, state):
        if state[-1] == l_map[100]:
            return 1, True
        else:
            return 0, False

    def reconstruct_sequence(self, state_trace):
        np_st = np.array(state_trace)
        upper = list(np_st[:, 0])
        lower = [state_trace[0][2]]
        for ii in range(len(state_trace)):
            lower += [np_st[ii, -1]]
        lower_midi_orig = [l_inv_map[li] for li in lower]
        # double remap is to avoid pruned out actions and still get the right result
        pp_map = {}
        for k, v in self.valid_action_remapper.items():
            pp_map[k] = self.valid_action_inv_map[v]
        # add back the invalid action to handle first step decoding
        pp_map[p_map[97]] = 97
        self.pp_map = pp_map
        upper_interval_orig = [pp_map[pi] for pi in upper]
        # 97 is the boundary for special start, end of sequence stuff
        lower_midi = [lm for lm in lower_midi_orig if lm < 97]
        lower_midi = np.array(lower_midi) + self.offset_value
        upper_interval = [ui for ui in upper_interval_orig if ui < 97]
        upper_midi = np.array(upper_interval) + lower_midi
        midi = [[um for um in upper_midi], [lm for lm in lower_midi]]
        return midi

    def evaluate_sequence(self, midi_sequence):
        parts = midi_sequence
        durations = [['4'] * len(p) for p in parts]
        key_signature = "C"
        time_signature = "4/4"
        aok = analyze_two_voices(parts, durations, key_signature, time_signature,
                                 species="species1", cantus_firmus_voices=[1])
        return aok


random_state = np.random.RandomState(9)
move_validator = MusicStateManager(random_state=random_state)
pv = PolicyValueNetwork(lower_size=len(l_map), prev_size=len(p_map), policy_size=move_validator.valid_action_size)

def policy_value_fn(state):
    p, l = state[0][None, None], state[1:][None]
    p_, l_ = Variable(th.FloatTensor(p)), Variable(th.FloatTensor(l))
    policy_log_probs, value_est = pv(p_, l_)
    policy_log_probs = policy_log_probs.data.numpy()
    value_est = value_est.data.numpy()
    policy_probs = np.exp(policy_log_probs).flatten()
    actions = move_validator.valid_actions(state)
    assert len(actions) == len(policy_probs)
    comb = tuple(zip(actions, policy_probs))
    return comb, float(value_est.ravel())

"""
state = state_mgr.init_state_
policy_value_fn(state)
ii = 0
while True:
    action = 5
    winner, end = state_mgr.finished(state)
    if not end:
        next_state = state_mgr.next_state(state, action)
        state = next_state
        ii += 1
    else:
        break
"""

def get_trace(random_state):
    state_mgr = MusicStateManager(random_state=random_state)
    mcts = NetMCTS(policy_value_fn, state_mgr, random_state=random_state)
    state = mcts.state_manager.init_state_
    temp = 1.
    states, moves, mcts_probs = [], [], []
    step = 0
    while True:
        move, move_probs = mcts.get_action(state, temp=temp)
        states.append(state)
        moves.append(move)
        mcts_probs.append(move_probs)
        mcts.update_to_move(move)
        state = mcts.state_manager.next_state(state, move)
        winner, end = mcts.state_manager.finished(state)
        step += 1
        if end:
            # Hack to end on octave or unison
            min_dist = np.inf
            min_poss = None
            for poss in [-16, -8, 0, 8, 16]:
                dist = abs(poss - p_inv_map[state[0]])
                if dist < min_dist:
                    min_poss = poss
                    min_dist = dist
            # need to use the full map for decoding, since valid actions may be reduced
            estate = np.array([p_map[min_poss], l_map[100], l_map[100], l_map[100]])
            full_seq = list(states) + [state, estate]
            try:
                midi = mcts.state_manager.reconstruct_sequence(full_seq)
            except:
                print("Error in midi gen")
                from IPython import embed; embed(); raise ValueError()

            try:
                musical_check = mcts.state_manager.evaluate_sequence(midi)
            except:
                print("Error in musical check")
                from IPython import embed; embed(); raise ValueError()

            break
    return states, mcts_probs, moves, midi, musical_check

if __name__ == "__main__":
    from visualization import pitches_and_durations_to_pretty_midi
    from visualization import plot_pitches_and_durations
    from analysis import fixup_parts_durations
    from analysis import intervals_from_midi

    from collections import deque
    import cPickle as pickle
    import os
    import shutil

    save_path = "current_data_buffer.pkl"
    tmp_save_path = "current_data_buffer_tmp.pkl"
    lockfile = "lock.lock"
    boundary = 1000
    deque_max_size = 100000
    data_buffer = deque(maxlen=deque_max_size)

    seed = 1999
    if os.path.exists(save_path):
        with open(save_path, "rb") as f:
            old_data = pickle.load(f)
        data_buffer.extend(old_data)
        print("Loaded {} datapoints from previous save buffer".format(len(data_buffer)))
        rewards = [od[1] for od in old_data]
        seed = int(10000 * sum([abs(r) for r in rewards])) % 223145
        print("Setting new seed {}".format(seed))

    random_state = np.random.RandomState(seed)
    n_traces = 0
    while True:
        trace_data = []
        n_traces += 1
        i = 1
        ss = 0
        while True:
            print("Trace {}, step {}, total length {}".format(n_traces, i, ss))
            trace_random_state = np.random.RandomState(random_state.randint(1000000000))
            trace_results = get_trace(trace_random_state)
            trace_data.append(trace_results)
            ss = sum([len(td[1]) for td in trace_data])
            i += 1
            if ss > boundary:
                break

        # scaled rewards are from 0-1, with 1 being a complete sequence correct
        scaled_reward = [min(td[-1][1]["False"]) / float(len(td[-1][2][0])) for td in trace_data]
        scaled_reward = [sr if sr > 0 else -1. for sr in scaled_reward]
        print("Average scaled rewards: {}".format(np.mean(scaled_reward)))
        print("Min scaled rewards: {}".format(np.min(scaled_reward)))
        print("Max scaled rewards: {}".format(np.max(scaled_reward)))

        trace_mcts_probs = [td[1] for td in trace_data]
        trace_mcts_rewards = [[scaled_reward[n]] * len(td[1]) for n, td in enumerate(trace_data)]

        def safezip(a, b):
            assert len(a) == len(b)
            return list(zip(a, b))

        for tmp, tmr in safezip(trace_mcts_probs, trace_mcts_rewards):
            data_buffer.extend(safezip(tmp, tmr))

        with open(tmp_save_path, "wb") as f:
            pickle.dump(list(data_buffer), f)

        if os.path.exists(lockfile):
            while True:
                time.sleep(2)
                if not os.path.exists(lockfile):
                    break

        shutil.move(tmp_save_path, save_path)
        print("Wrote buffer data of length {} to {}".format(len(data_buffer), save_path))

        # plot the best output trace
        argmax = [n for n, sr in enumerate(scaled_reward) if sr == max(scaled_reward)][0]
        argmin = [n for n, sr in enumerate(scaled_reward) if sr == min(scaled_reward)][0]
        all_parts = []
        all_durations = []
        for ai in [argmax, argmin]:
            if ai == argmax:
                print("Plotting best example {}".format(ai))
            else:
                print("Plotting worst example {}".format(ai))
            #parts = trace_data[0][-2]
            parts = trace_data[ai][-2]
            durations = [['4'] * len(p) for p in parts]
            interval_figures = intervals_from_midi(parts, durations)
            _, interval_durations = fixup_parts_durations(parts, durations)
            interval_durations = [interval_durations[0]]
            durations = [[int(di) for di in d] for d in durations]
            all_parts.append(parts)
            all_durations.append(durations)

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
        print("Trace {} completed".format(n_traces))
