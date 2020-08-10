# Original source from
# https://gist.github.com/Tushar-N/dfca335e370a2bc3bc79876e6270099e
"""
主要介绍 pack_padded_sequence 函数 和 pad_packed_sequence 函数的用法
"""

import torch
import torch.nn as nn
from torch.autograd import Variable
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import torch.nn.functional as F
import numpy as np
import itertools


def flatten(l):
    return list(itertools.chain.from_iterable(l))  # 每一个单词分成字母, 并且排序


seqs = ['ghatmasala', 'nicela', 'chutpakodas']  # length= [10, 6, 11]

# make <pad> idx 0
vocab = ['<pad>'] + sorted(list(set(flatten(seqs))))  # 词典列表

# make model
embedding_size = 3
embed = nn.Embedding(len(vocab), embedding_size)
lstm = nn.LSTM(embedding_size, 5)
# convert sequence to vocab id vector
vectorized_seqs = [[vocab.index(tok) for tok in seq] for seq in seqs]  # 字符串转化为index序列
print("vectorized_seqs", vectorized_seqs)

# get the length of each seq in your batch
seq_lengths = torch.LongTensor([x for x in map(len, vectorized_seqs)])  # 每个字符长度[10, 6, 11]转tensor


# dump padding everywhere, and place seqs on the left.
# NOTE: you only need a tensor as big as your longest sequence
seq_tensor = Variable(torch.zeros((len(vectorized_seqs), seq_lengths.max()))).long()  # [3 x 11]的零向量
for idx, (seq, seqlen) in enumerate(zip(vectorized_seqs, seq_lengths)):
    seq_tensor[idx, :seqlen] = torch.LongTensor(seq)


# SORT YOUR TENSORS BY LENGTH!
seq_lengths, perm_idx = seq_lengths.sort(0, descending=True)
seq_tensor = seq_tensor[perm_idx]  # 按照降序进行排列之后的长度值

# utils.rnn lets you give (B,L,D) tensors where B is the batch size, L is the maxlength, if you use batch_first=True
# Otherwise, give (L,B,D) tensors
seq_tensor = seq_tensor.transpose(0, 1)  # (Batch_size, seq_Len, D) -> (seq_Len, Batch_size, D)
print("seq_tensor after transposing\n", seq_tensor.size())

# embed your sequences 加入embedding
embeded_seq_tensor = embed(seq_tensor)  # 11 x 3 x 3, 从这里开始进入pack_padded_sequence

# pack them up nicely (compress the data) 输入的是按照长度从长到短的序列和长度列表
packed_input = pack_padded_sequence(embeded_seq_tensor, seq_lengths.cpu().numpy())  # seq_lenth需要从大到小排列才可以

# throw them through your LSTM (remember to give batch_first=True here if you packed with it)
packed_output, (ht, ct) = lstm(packed_input)  # packed_input 输入是 27 x 3  #总共是27的有效长度, 输出是27x5
# unpack your output if required  解压缩即可
output, _ = pad_packed_sequence(packed_output)
print("Lstm output\n", output.size())  # [seq_len, batch, hidden_dim] = [11 x 3 x 5]
unpackout, (h, c) = lstm(embeded_seq_tensor)  # 不需要压缩直接进行lstm单元计算
# Or if you just want the final hidden state?
print("Last output\n", ht[-1].size(), ht[-1].data)
