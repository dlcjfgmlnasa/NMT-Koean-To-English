# -*- coding:utf-8 -*-
import torch
import torch.nn as nn


class EncoderRNN(nn.Module):
    def __init__(self, embedding, rnn_dim, n_layer=1, dropout=0):
        super(EncoderRNN, self).__init__()
        self.embedding = embedding
        self.rnn_dim = rnn_dim
        self.n_layers = n_layer

        embedding_dim = embedding.embedding_dim
        self.rnn = nn.LSTM(embedding_dim, rnn_dim, n_layer, dropout=dropout, batch_first=True)
        # nn.LSTM
        # batch_first = False : (seq_len, batch_size, dims)
        # batch_first = True  : (batch_size, seq_len, dims)

    def forward(self, inputs, length):
        # input => (batch_size, time_step)

        embedded = self.embedding(inputs)               # => (batch_size, time_step, dimension)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, length, batch_first=True)
        outputs, (hidden, cell) = self.rnn(packed)      # => (batch_size, time_step, rnn_dim)
        outputs, _ = nn.utils.rnn.pad_packed_sequence(outputs, batch_first=True)    # => (batch_size, seq len, rnn_dims)
        del outputs

        return hidden, cell


class DecoderRNN(nn.Module):
    def __init__(self, embedding, rnn_dim, out_dim, n_layer=1, dropout=0):
        super(DecoderRNN, self).__init__()
        self.embedding = embedding
        self.rnn_dim = rnn_dim
        self.out_dim = out_dim
        self.n_layer = n_layer

        embedding_dim = embedding.embedding_dim
        self.rnn = nn.LSTM(embedding_dim, rnn_dim, n_layer, dropout=dropout, batch_first=True)
        # nn.LSTM
        # batch_first = False : (seq_len, batch_size, dims)
        # batch_first = True  : (batch_size, seq_len, dims)
        self.out = nn.Linear(rnn_dim, out_dim)

    def forward(self, inputs, last_hidden, last_cell):
        # inputs => (batch_size)
        # last_hidden => (n_layer, batch_size, rnn_dim)
        # last_cell => (n_layer, batch_size, rnn_dim)

        embedded = self.embedding(inputs)               # => (batch_size, dimension)
        embedded = embedded.unsqueeze(1)                # => (batch_size, 1, dimension)

        output, (hidden, cell) = self.rnn(embedded, (last_hidden, last_cell))   # => (batch_size, 1, rnn_dim)
        output = output.squeeze(1)                      # => (batch_size, rnn_dim)
        predication = self.out(output)                  # => (batch_size, voc_size)
        return predication, hidden, cell


class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder):
        super(Seq2Seq, self).__init__()
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, src_input, src_length, trg_input):
        # src_input => (batch_size, dimension)
        # trg_input => (batch_size, dimension)
        hidden, cell = self.encoder(src_input, src_length)

        batch_size = trg_input.shape[0]
        max_len = trg_input.shape[1]
        trg_vocab_size = self.decoder.out_dim

        outputs = torch.zeros(batch_size, max_len, trg_vocab_size)  # => (batch_size, seq_len, voc_size)
        input_ = trg_input[:, 0]                        # => (batch_size)

        for t in range(1, max_len):
            predication, hidden, cell = self.decoder(input_, hidden, cell)
            outputs[:, t] = predication
            values, indices = predication.max(dim=1)
            del values
            input_ = indices

        return outputs                                  # => (batch_size, seq_len, voc_size)
