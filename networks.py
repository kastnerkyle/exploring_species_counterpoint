import torch as th
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F
import torch.optim as optim

import numpy as np


class PolicyValueNetwork(nn.Module):
    def __init__(self, lower_size, prev_size, hidden_size=64, proj_size=32):
        super(PolicyValueNetwork, self).__init__()
        self.value_size = 1
        self.lower_size = lower_size
        self.prev_size = prev_size
        self.policy_size = prev_size
        self.hidden_size = hidden_size
        self.proj_size = proj_size
        #input_size = 12
        #proj_size = 50
        #n_layers = 1
        self.embed_l1 = nn.Embedding(self.lower_size, self.hidden_size)
        self.embed_l2 = nn.Embedding(self.lower_size, self.hidden_size)
        self.embed_l3 = nn.Embedding(self.lower_size, self.hidden_size)
        self.embed_p = nn.Embedding(self.prev_size, self.hidden_size)

        self.joint_linear1 = nn.Linear(4 * self.hidden_size, self.hidden_size)
        self.joint_linear2 = nn.Linear(self.hidden_size, self.hidden_size)

        self.value_linear = nn.Linear(self.hidden_size, self.proj_size)
        self.value_pred = nn.Linear(self.proj_size, self.value_size)

        self.policy_linear = nn.Linear(self.hidden_size, self.proj_size)
        self.policy_pred = nn.Linear(self.proj_size, self.policy_size)

    def forward(self, x_p, x_l):
        # x_p is the previous interval chosen in the upper voice
        # x_l is window of 3 steps of the bottom voice
        x_p_i = x_p.long()
        x_l_i = x_l.long()
        x_p_e = self.embed_p(x_p_i[:, 0])
        x_l_e1 = self.embed_l1(x_l_i[:, 0])
        x_l_e2 = self.embed_l2(x_l_i[:, 1])
        x_l_e3 = self.embed_l3(x_l_i[:, 2])

        joined = th.cat([x_p_e, x_l_e1, x_l_e2, x_l_e3], dim=-1)
        l1 = self.joint_linear1(joined)
        r_l1 = F.relu(l1)
        l2 = self.joint_linear2(r_l1)
        r_l2 = F.relu(l2)

        po_l1 = self.policy_linear(r_l2)
        r_po_l1 = F.relu(po_l1)
        po_l2 = self.policy_pred(r_po_l1)
        p_po_l2 = F.log_softmax(po_l2, dim=1)

        v_l1 = self.value_linear(r_l2)
        r_v_l1 = F.relu(v_l1)
        v_l2 = self.value_pred(r_v_l1)
        p_v_l2 = F.tanh(v_l2)
        return p_po_l2, p_v_l2


if __name__ == "__main__":
    # toy example of the full pipeline
    from datasets import fetch_two_voice_species1
    from datasets import fetch_three_voice_species1
    from analysis import notes_to_midi

    all_ex = fetch_two_voice_species1()
    # for now, just get info from 2 voice species 1
    #all_ex += fetch_three_voice_species1()
    all_tb = []
    all_lower_midi = []
    all_upper_midi = []
    all_lower_offset = []
    all_upper_offset = []
    for ex in all_ex:
        # skip any "wrong" examples
        if not all(ex["answers"]):
            continue
        nd = ex["notes_and_durations"]
        notes = [[ndii[0] for ndii in ndi] for ndi in nd]
        # durations not used in first species, leave it alone
        durations = [[ndii[1] for ndii in ndi] for ndi in nd]
        midi = notes_to_midi(notes)
        cf = ex["cantus_firmus_voice"]

        all_lower_offset.append(list(np.array(midi[1]) - midi[1][-1]) + [13])
        all_upper_offset.append(list(np.array(midi[0]) - midi[0][-1]))

        all_upper_midi.append(midi[0])
        all_lower_midi.append(midi[1])

        tb = list(np.array(midi[0]) - np.array(midi[1]))
        all_tb.append(tb)

    flat_tb = [ddd for dd in all_tb for ddd in dd]
    # these are the actions
    # they map to intervals wrt bottom voice
    # [-8, -4, -3, 0, 3, 4, 7, 8, 9, 12, 15, 16]
    tb_set = sorted(list(set(flat_tb)))
    tb_map = {v: k for k, v in enumerate(tb_set)}
    tb_rev_map = {v: k for k, v in tb_map.items()}

    flat_lower_offset = [ddd for dd in all_lower_offset for ddd in dd]
    # these are input symbols from bottom_voice, as offsets relative to last note ("key" centered)
    # [-12, -10, -9, -7, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 8, 9, 12, 13]
    # 13 reserved for end of lower indicator
    lower_offset_set = sorted(list(set(flat_lower_offset)))
    lower_map = {v: k for k, v in enumerate(lower_offset_set)}
    lower_rev_map = {v: k for k, v in lower_map.items()}

    def make_windows(all_tb, all_lower_offset, lower_window=3, upper_lookback=1):
        # not general
        assert upper_lookback < lower_window
        all_instances = []
        for ii in range(len(all_tb)):
            tb = all_tb[ii]
            lower_offset = all_lower_offset[ii]
            instances = []
            for kk in range(upper_lookback, len(lower_offset) - lower_window + lower_window // 2 + 1):
                lookback = tb[kk - upper_lookback:kk]
                window = lower_offset[kk - upper_lookback:kk + lower_window - upper_lookback]
                instances.append([lookback, window])
            all_instances += instances
        return all_instances

    list_data = make_windows(all_tb, all_lower_offset)
    data_p = np.array([[tb_map[ldi] for ldi in ld[0]] for ld in list_data])
    data_l = np.array([[lower_map[ldi] for ldi in ld[1]] for ld in list_data])

    pv = PolicyValueNetwork(lower_size=len(lower_map), prev_size=len(tb_map))

    optimizer = optim.Adam(pv.parameters(), lr=0.0001, weight_decay=1E-4)
    optimizer.zero_grad()

    mb_p = Variable(th.FloatTensor(data_p[:5]))
    mb_l = Variable(th.FloatTensor(data_l[:5]))

    np_po_gt = np.ones((5, len(tb_map))) / float(len(tb_map))
    np_v_gt = 0. * np.ones((5, 1)) + 1.

    gt_po = Variable(th.FloatTensor(np_po_gt))
    gt_v = Variable(th.FloatTensor(np_v_gt))

    for i in range(10000):
        policy_log_probs, value_est = pv(mb_p, mb_l)

        v_loss = th.sum(((value_est - gt_v) ** 2) / gt_po.size()[0])
        po_loss = -th.sum((gt_po * policy_log_probs) / gt_po.size()[0])

        loss = po_loss + v_loss
        print("v", v_loss.data[0])
        print("p", po_loss.data[0])
        print("l", loss.data[0])
        loss.backward()
        optimizer.step()
    from IPython import embed; embed(); raise ValueError()


