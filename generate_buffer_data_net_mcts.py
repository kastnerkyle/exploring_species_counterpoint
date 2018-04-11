from net_mcts import NetMCTS
from networks import PolicyValueNetwork
from env_managers import MusicStateManager
import numpy as np
import torch as th
from torch.autograd import Variable
import copy

random_state = np.random.RandomState(9)
move_validator = MusicStateManager(random_state=random_state)
pv = PolicyValueNetwork(lower_size=len(move_validator.guide_map), prev_size=len(move_validator.original_map),
                        policy_size=move_validator.valid_action_size)

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
            states.append(state)
            # add some flourish to the end / close it off
            full_seq = mcts.make_full_sequence(list(states))
            try:
                midi = mcts.state_manager.reconstruct_sequence(full_seq)
            except:
                print("Error in midi gen")
                from IPython import embed; embed(); raise ValueError()

            try:
                musical_check = mcts.state_manager.evaluate_sequence(midi)
            except:
                print("Error in trace musical check")
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
    import gzip
    import time

    from shared_config import save_path, tmp_save_path, lockfile, model_path
    from shared_utils import creation_date

    boundary = 1000
    deque_max_size = 100000
    data_buffer = deque(maxlen=deque_max_size)

    seed = 1999
    if os.path.exists(save_path):
        with gzip.open(save_path, "rb") as f:
            old_data = pickle.load(f)
        data_buffer.extend(old_data)
        print("Loaded {} datapoints from previous save buffer {}".format(len(data_buffer), save_path))
        rewards = [od[-1] for od in old_data]
        seed = int(10000 * sum([abs(r) for r in rewards])) % 223145
        print("Setting new seed {}".format(seed))

    random_state = np.random.RandomState(seed)
    n_traces = 0

    last_param_info = None
    while True:
        ncd = creation_date(model_path)
        if last_param_info is None or ncd != last_param_info:
            print("Detected new model parameters in {}, reloading".format(model_path))
            pv.load_state_dict(th.load(model_path, map_location=lambda storage, loc: storage))

        start_time = time.time()
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
        stop_time = time.time()

        try:
            # this hackery mainly to avoid empty sequence edge cases
            # tf[-1][1]["True"] cannot be 0 length if tf[-1][1]["False"] is len 0
            failed = [min(td[-1][1]["False"] + [len(td[-2][0])]) for td in trace_data]
            reward = [[1. if ni < failed[n] else -1. for ni in range(len(td[-2][0]))]
                       for n, td in enumerate(trace_data)]
        except:
            print("Issue in scaled reward calculation")
            from IPython import embed; embed(); raise ValueError()

        flat_reward = [ri for r in reward for ri in r]

        print("Average scaled rewards: {}".format(np.mean(flat_reward)))
        print("Min scaled rewards: {}".format(np.min(flat_reward)))
        print("Max scaled rewards: {}".format(np.max(flat_reward)))
        # cut off the end state, since it has no prob transition (it was terminal)
        trace_mcts_states = [td[0][:-1] for td in trace_data]
        trace_mcts_probs = [td[1] for td in trace_data]
        # cut off the end reward, since it has no prob transition (it was terminal)
        trace_mcts_rewards = [reward[n][:len(trace_mcts_probs[n])] for n, td in enumerate(trace_data)]

        def safezip(a, b, c=None):
            assert len(a) == len(b)
            if c:
                assert len(a) == len(c)
                return list(zip(a, b, c))
            else:
                return list(zip(a, b))

        for tms, tmp, tmr in safezip(trace_mcts_states, trace_mcts_probs, trace_mcts_rewards):
            data_buffer.extend(safezip(tms, tmp, tmr))

        with gzip.open(tmp_save_path, "wb") as f:
            pickle.dump(list(data_buffer), f)

        if os.path.exists(lockfile):
            while True:
                print("Buffer lockfile {} found, sleeping...".format(lockfile))
                time.sleep(2)
                if not os.path.exists(lockfile):
                    break

        shutil.move(tmp_save_path, save_path)
        print("Wrote buffer data of length {} to {}, time to generate {} seconds".format(len(data_buffer), save_path, int(stop_time - start_time)))

        # plot the best and worst output trace
        argmax = [n for n, sr in enumerate(reward) if sr == max(reward)][0]
        argmin = [n for n, sr in enumerate(reward) if sr == min(reward)][0]
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
