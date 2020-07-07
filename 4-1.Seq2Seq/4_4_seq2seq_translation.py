import unicodedata
import string
import re
import random
import time
import math
import torch
import torch.nn as nn
from torch.autograd import Variable
from torch import optim
import torch.nn.functional as F

USE_CUDA = True
SOS_token = 0
EOS_token = 1


class Lang:
    def __init__(self, name):
        self.name = name
        self.word2index = {}
        self.word2count = {}
        self.index2word = {0: "SOS", 1: "EOS"}
        self.n_words = 2  # Count SOS and EOS

    def index_words(self, sentence):
        for word in sentence.split(' '):
            self.index_word(word)

    def index_word(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1


# Turn a Unicode string to plain ASCII, thanks to http://stackoverflow.com/a/518232/2809427
def unicode_to_ascii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )


# Lowercase, trim, and remove non-letter characters
def normalize_string(s):
    s = unicode_to_ascii(s.lower().strip())
    s = re.sub(r"([.!?])", r" \1", s)
    s = re.sub(r"[^a-zA-Z.!?]+", r" ", s)
    return s


def read_langs(lang1, lang2, reverse=False):
    print("Reading lines...")

    # Read the file and split into lines
    lines = open('../eng-fra/%s-%s.txt' % (lang1, lang2)).read().strip().split('\n')

    # Split every line into pairs and normalize
    # pair = list()
    # for l in lines:
    #     temp = list()
    #     for s in l.split('\t')[0:2]:
    #         temps = normalize_string(s)
    #         temp.append(temps)
    #     pair.append(temp)

    pairs = [[normalize_string(s) for s in l.split('\t')[0:2]] for l in lines]

    # Reverse pairs, make Lang instances
    if reverse:
        pairs = [list(reversed(p)) for p in pairs]
        input_lang = Lang(lang2)
        output_lang = Lang(lang1)
    else:
        input_lang = Lang(lang1)
        output_lang = Lang(lang2)

    return input_lang, output_lang, pairs


MAX_LENGTH = 10

good_prefixes = (
    "i am ", "i m ",
    "he is", "he s ",
    "she is", "she s",
    "you are", "you re "
)


def filter_pair(p):
    return len(p[0].split(' ')) < MAX_LENGTH and len(p[1].split(' ')) < MAX_LENGTH and p[1].startswith(good_prefixes)


def filter_pairs(pairs):
    return [pair for pair in pairs if filter_pair(pair)]


def prepare_data(lang1_name, lang2_name, reverse=False):
    input_lang, output_lang, pairs = read_langs(lang1_name, lang2_name, reverse)
    print("Read %s sentence pairs" % len(pairs))

    pairs = filter_pairs(pairs)
    print("Trimmed to %s sentence pairs" % len(pairs))

    print("Indexing words...")
    for pair in pairs:
        input_lang.index_words(pair[0])
        output_lang.index_words(pair[1])

    return input_lang, output_lang, pairs


input_lang, output_lang, pairs = prepare_data('eng', 'fra', False)

# Print an example pair
print(random.choice(pairs))


# Return a list of indexes, one for each word in the sentence
# def indexes_from_sentence(lang, sentence):
#     return [lang.word2index[word] for word in sentence.split(' ')]
#
#
# def variable_from_sentence(lang, sentence):
#     indexes = indexes_from_sentence(lang, sentence)
#     indexes.append(EOS_token)
#     var = Variable(torch.LongTensor(indexes).view(-1, 1))
#     #     print('var =', var)
#     if USE_CUDA: var = var.cuda()
#     return var
#
#
# def variables_from_pair(pair):
#     input_variable = variable_from_sentence(input_lang, pair[0])
#     target_variable = variable_from_sentence(output_lang, pair[1])
#     return (input_variable, target_variable)
#
#
# class EncoderRNN(nn.Module):
#     def __init__(self, input_size, hidden_size, n_layers=1):
#         super(EncoderRNN, self).__init__()
#
#         self.input_size = input_size
#         self.hidden_size = hidden_size
#         self.n_layers = n_layers
#
#         self.embedding = nn.Embedding(input_size, hidden_size)
#         self.gru = nn.GRU(hidden_size, hidden_size, n_layers)
#
#     def forward(self, word_inputs, hidden):
#         # Note: we run this all at once (over the whole input sequence)
#         seq_len = len(word_inputs)
#         embedded = self.embedding(word_inputs).view(seq_len, 1, -1)
#         output, hidden = self.gru(embedded, hidden)
#         return output, hidden
#
#     def init_hidden(self):
#         hidden = Variable(torch.zeros(self.n_layers, 1, self.hidden_size))
#         if USE_CUDA: hidden = hidden.cuda()
#         return hidden
