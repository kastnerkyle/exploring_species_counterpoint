from networks import PolicyValueNetwork
from env_managers import MusicStateManager
import numpy as np
from torch.autograd import Variable
import torch as th
import torch.optim as optim

random_state = np.random.RandomState(16)
move_validator = MusicStateManager(random_state=random_state)
pv = PolicyValueNetwork(lower_size=len(move_validator.guide_map), prev_size=len(move_validator.original_map),
                        policy_size=move_validator.valid_action_size)
optimizer = optim.Adam(pv.parameters(), lr=0.0001, weight_decay=1E-4)
optimizer.zero_grad()

if __name__ == "__main__":
    import cPickle as pickle
    import gzip
    import time
    import os

    from shared_config import save_path, tmp_save_path, lockfile, model_path
    from shared_utils import creation_date

    training_batches = 100000
    batch_size = 512
    print_update_every = 5000
    use_cuda = True

    training_random_state = np.random.RandomState(221)
    if os.path.exists(model_path):
        print("Reloading saved model parameters from {}".format(model_path))
        pv.load_state_dict(th.load(model_path))
    else:
        print("Previous model not found, saving initial model parameters to {}".format(model_path))
        th.save(pv.state_dict(), model_path)

    if use_cuda:
        pv = pv.cuda()

    last_load_info = None
    while True:
        # defensively kill lockfile if it is already there
        if os.path.exists(lockfile):
            print("Clearing pre-existing lockfile {}".format(lockfile))
            os.remove(lockfile)

        # do nothing til there's some data to train on
        if not os.path.exists(save_path):
            while True:
                print("No buffer data found at {}, sleeping...".format(save_path))
                time.sleep(10)
                if os.path.exists(save_path):
                    break

        ncd = creation_date(save_path)
        if last_load_info is None or ncd != last_load_info:
            if ncd != last_load_info:
                print("Detected change in saved buffer file {}".format(save_path))
            print("Writing lockfile {}".format(lockfile))
            open(lockfile, 'wb').close()

            with gzip.open(save_path, "rb") as f:
                data_buf = pickle.load(f)
                print("Loaded {} datapoints from save buffer {}".format(len(data_buf), save_path))

            print("Clearing lockfile {}".format(lockfile))
            os.remove(lockfile)
            last_load_info = creation_date(save_path)

        indices = np.arange(len(data_buf))
        train_states = np.array([db[0] for db in data_buf])
        train_mcts_probs = np.array([db[1] for db in data_buf])
        train_mcts_targets = np.array([db[2] for db in data_buf])

        #balance the minibatches
        indices_target_neg = np.where(train_mcts_targets < 0)[0]
        indices_target_pos = np.where(train_mcts_targets >= 0)[0]

        # sample indices *with replacement* for training_batches steps...
        tot = 0
        for step in range(training_batches):
            # be sure at least 12.5% are positives
            if len(indices_target_pos) > 0 and len(indices_target_neg) > 0:
                neg_mb_ind = training_random_state.choice(indices_target_neg, batch_size // 2)
                pos_mb_ind = training_random_state.choice(indices_target_pos, batch_size // 2)
                mb_ind = np.concatenate((neg_mb_ind, pos_mb_ind))
            else:
                mb_ind = training_random_state.choice(indices, int(batch_size))
            training_random_state.shuffle(mb_ind)
            mb_states = train_states[mb_ind]
            mb_probs = train_mcts_probs[mb_ind]
            mb_target = train_mcts_targets[mb_ind]
            p = mb_states[:, 0][:, None]
            l = mb_states[:, 1:]
            p_, l_ = Variable(th.FloatTensor(p)), Variable(th.FloatTensor(l))
            gt_po = Variable(th.FloatTensor(mb_probs))
            gt_v = Variable(th.FloatTensor(mb_target))
            if use_cuda:
                p_ = p_.cuda()
                l_ = l_.cuda()
                gt_po = gt_po.cuda()
                gt_v = gt_v.cuda()

            policy_log_probs, value_est = pv(p_, l_)

            v_loss = th.mean(((value_est - gt_v) ** 2))
            po_loss = -th.mean(th.sum(gt_po * policy_log_probs, dim=1))

            loss = po_loss + v_loss
            comb_loss = loss.cpu().data.numpy()[0]
            tot += comb_loss
            loss.backward()
            optimizer.step()
            if step > 100 and (step % print_update_every) == 0:
                print("Average loss after step {}: {}".format(step, tot / float(step + 1)))

        # save parameters
        print("Saving current model parameters to {}".format(model_path))
        th.save(pv.state_dict(), model_path)
