# -*- coding: utf-8 -*-
"""Graduate_Assessment_CRF_BJ68299.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XhQH_A0xW32yi9aSH3HC7VT1TjXmWdyM
"""

!pip install -qq datasets conll

pip install conllu

from datasets import load_dataset
from collections import defaultdict

# ud data for pos tagging
dataset = load_dataset('universal_dependencies', 'en_ewt')

def build_vocab(data):
    word_vocab = defaultdict(lambda: len(word_vocab))
    tag_vocab = defaultdict(lambda: len(tag_vocab))

    # special tokens
    word_vocab["<PAD>"]
    word_vocab["<UNK>"]
    tag_vocab["<PAD>"]
    tag_vocab["<UNK>"]

    for sentence in data['train']:
        for word in sentence['tokens']:
            word_vocab[word]
        for tag in sentence['deprel']:
            tag_vocab[tag]

    return dict(word_vocab), dict(tag_vocab)

word_to_idx, tag_to_idx = build_vocab(dataset)

print(f"Number of unique words: {len(word_to_idx)}")
print(f"Number of unique tags: {len(tag_to_idx)}")

print(word_to_idx)
print(tag_to_idx)


import json

with open('word_to_idx.json', 'w') as f:
    json.dump(word_to_idx, f)

with open('tag_to_idx.json', 'w') as f:
    json.dump(tag_to_idx, f)



from datasets import load_dataset
import torch
from torch.utils.data import Dataset, DataLoader

# Load the Universal Dependencies dataset for POS tagging
dataset = load_dataset('universal_dependencies', 'en_ewt')

# Example class to convert the dataset into a PyTorch Dataset
class UDDataset(Dataset):
    def __init__(self, data, word_to_idx, tag_to_idx, max_length):
        self.data = data
        self.word_to_idx = word_to_idx
        self.tag_to_idx = tag_to_idx
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Get the sentence
        sentence = self.data[idx]['tokens']
        # Convert sentence to idx
        sentence_idx = [self.word_to_idx.get(word, self.word_to_idx["<UNK>"]) for word in sentence]

        # Get the tags
        tags = self.data[idx]['deprel']
        # Convert tags to idx
        tags_idx = [self.tag_to_idx[tag] for tag in tags]

        # Padding
        sentence_idx += [self.word_to_idx["<PAD>"]] * (self.max_length - len(sentence_idx))
        tags_idx += [self.tag_to_idx["<PAD>"]] * (self.max_length - len(tags_idx))

        return torch.tensor(sentence_idx[:self.max_length]), torch.tensor(tags_idx[:self.max_length])

# Create word_to_idx and tag_to_idx dictionaries
# word_to_idx = {"<PAD>": 0, "<UNK>": 1, ...} # Add your word-to-index mappings
# tag_to_idx = {"<PAD>": 0, "<UNK>": 1, ...} # Add your tag-to-index mappings
max_length = 100  # Define the maximum sequence length

# Create the PyTorch datasets
train_dataset = UDDataset(dataset['train'], word_to_idx, tag_to_idx, max_length)
valid_dataset = UDDataset(dataset['validation'], word_to_idx, tag_to_idx, max_length)
test_dataset = UDDataset(dataset['test'], word_to_idx, tag_to_idx, max_length)
'''
print("Train Dataset")
print(train_dataset)

print("Valid Dataset")
print(valid_dataset)

print("Test Dataset")
print(test_dataset)
'''
# Create the DataLoaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
valid_loader = DataLoader(valid_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

__version__ = '0.7.2'

from typing import List, Optional

import torch
import torch.nn as nn


class CRF(nn.Module):
    """Conditional random field.

    This module implements a conditional random field [LMP01]_. The forward computation
    of this class computes the log likelihood of the given sequence of tags and
    emission score tensor. This class also has `~CRF.decode` method which finds
    the best tag sequence given an emission score tensor using `Viterbi algorithm`_.

    Args:
        num_tags: Number of tags.
        batch_first: Whether the first dimension corresponds to the size of a minibatch.

    Attributes:
        start_transitions (`~torch.nn.Parameter`): Start transition score tensor of size
            ``(num_tags,)``.
        end_transitions (`~torch.nn.Parameter`): End transition score tensor of size
            ``(num_tags,)``.
        transitions (`~torch.nn.Parameter`): Transition score tensor of size
            ``(num_tags, num_tags)``.


    .. [LMP01] Lafferty, J., McCallum, A., Pereira, F. (2001).
       "Conditional random fields: Probabilistic models for segmenting and
       labeling sequence data". *Proc. 18th International Conf. on Machine
       Learning*. Morgan Kaufmann. pp. 282–289.

    .. _Viterbi algorithm: https://en.wikipedia.org/wiki/Viterbi_algorithm
    """

    def __init__(self, num_tags: int, batch_first: bool = False) -> None:
        if num_tags <= 0:
            raise ValueError(f'invalid number of tags: {num_tags}')
        super().__init__()
        self.num_tags = num_tags
        self.batch_first = batch_first
        self.start_transitions = nn.Parameter(torch.empty(num_tags))
        self.end_transitions = nn.Parameter(torch.empty(num_tags))
        self.transitions = nn.Parameter(torch.empty(num_tags, num_tags))

        self.reset_parameters()

    def reset_parameters(self) -> None:
        """Initialize the transition parameters.

        The parameters will be initialized randomly from a uniform distribution
        between -0.1 and 0.1.
        """
        nn.init.uniform_(self.start_transitions, -0.1, 0.1)
        nn.init.uniform_(self.end_transitions, -0.1, 0.1)
        nn.init.uniform_(self.transitions, -0.1, 0.1)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(num_tags={self.num_tags})'

    def forward(
            self,
            emissions: torch.Tensor,
            tags: torch.LongTensor,
            mask: Optional[torch.ByteTensor] = None,
            reduction: str = 'sum',
    ) -> torch.Tensor:
        """Compute the conditional log likelihood of a sequence of tags given emission scores.

        Args:
            emissions (`~torch.Tensor`): Emission score tensor of size
                ``(seq_length, batch_size, num_tags)`` if ``batch_first`` is ``False``,
                ``(batch_size, seq_length, num_tags)`` otherwise.
            tags (`~torch.LongTensor`): Sequence of tags tensor of size
                ``(seq_length, batch_size)`` if ``batch_first`` is ``False``,
                ``(batch_size, seq_length)`` otherwise.
            mask (`~torch.ByteTensor`): Mask tensor of size ``(seq_length, batch_size)``
                if ``batch_first`` is ``False``, ``(batch_size, seq_length)`` otherwise.
            reduction: Specifies  the reduction to apply to the output:
                ``none|sum|mean|token_mean``. ``none``: no reduction will be applied.
                ``sum``: the output will be summed over batches. ``mean``: the output will be
                averaged over batches. ``token_mean``: the output will be averaged over tokens.

        Returns:
            `~torch.Tensor`: The log likelihood. This will have size ``(batch_size,)`` if
            reduction is ``none``, ``()`` otherwise.
        """
        self._validate(emissions, tags=tags, mask=mask)
        if reduction not in ('none', 'sum', 'mean', 'token_mean'):
            raise ValueError(f'invalid reduction: {reduction}')
        if mask is None:
            mask = torch.ones_like(tags, dtype=torch.uint8)

        if self.batch_first:
            emissions = emissions.transpose(0, 1)
            tags = tags.transpose(0, 1)
            mask = mask.transpose(0, 1)

        # shape: (batch_size,)
        numerator = self._compute_score(emissions, tags, mask)
        # shape: (batch_size,)
        denominator = self._compute_normalizer(emissions, mask)
        # shape: (batch_size,)
        llh = numerator - denominator

        if reduction == 'none':
            return llh
        if reduction == 'sum':
            return llh.sum()
        if reduction == 'mean':
            return llh.mean()
        assert reduction == 'token_mean'
        return llh.sum() / mask.type_as(emissions).sum()

    def decode(self, emissions: torch.Tensor,
               mask: Optional[torch.ByteTensor] = None) -> List[List[int]]:
        """Find the most likely tag sequence using Viterbi algorithm.

        Args:
            emissions (`~torch.Tensor`): Emission score tensor of size
                ``(seq_length, batch_size, num_tags)`` if ``batch_first`` is ``False``,
                ``(batch_size, seq_length, num_tags)`` otherwise.
            mask (`~torch.ByteTensor`): Mask tensor of size ``(seq_length, batch_size)``
                if ``batch_first`` is ``False``, ``(batch_size, seq_length)`` otherwise.

        Returns:
            List of list containing the best tag sequence for each batch.
        """
        # self._validate(emissions, mask=mask)
        if mask is None:
            mask = emissions.new_ones(emissions.shape[:2], dtype=torch.uint8)

        if self.batch_first:
            emissions = emissions.transpose(0, 1)
            mask = mask.transpose(0, 1)

        return self._viterbi_decode(emissions, mask)

    def _validate(
            self,
            emissions: torch.Tensor,
            tags: Optional[torch.LongTensor] = None,
            mask: Optional[torch.ByteTensor] = None) -> None:
        if emissions.dim() != 3:
            raise ValueError(f'emissions must have dimension of 2, got {emissions.dim()}')
        if emissions.size(2) != self.num_tags:
            raise ValueError(
                f'expected last dimension of emissions is {self.num_tags}, '
                f'got {emissions.size(2)}')

        if tags is not None:
            if emissions.shape[:2] != tags.shape:
                raise ValueError(
                    'the first two dimensions of emissions and tags must match, '
                    f'got {tuple(emissions.shape[:2])} and {tuple(tags.shape)}')

        if mask is not None:
            if emissions.shape[:2] != mask.shape:
                raise ValueError(
                    'the first two dimensions of emissions and mask must match, '
                    f'got {tuple(emissions.shape[:2])} and {tuple(mask.shape)}')
            no_empty_seq = not self.batch_first and mask[0].all()
            no_empty_seq_bf = self.batch_first and mask[:, 0].all()
            if not no_empty_seq and not no_empty_seq_bf:
                raise ValueError('mask of the first timestep must all be on')

    def _compute_score(
            self, emissions: torch.Tensor, tags: torch.LongTensor,
            mask: torch.ByteTensor) -> torch.Tensor:
        # emissions: (seq_length, batch_size, num_tags)
        # tags: (seq_length, batch_size)
        # mask: (seq_length, batch_size)
        assert emissions.dim() == 3 and tags.dim() == 2
        assert emissions.shape[:2] == tags.shape
        assert emissions.size(2) == self.num_tags
        assert mask.shape == tags.shape
        assert mask[0].all()

        seq_length, batch_size = tags.shape
        mask = mask.type_as(emissions)

        # Start transition score and first emission
        # shape: (batch_size,)
        score = self.start_transitions[tags[0]]
        score += emissions[0, torch.arange(batch_size), tags[0]]

        for i in range(1, seq_length):
            # Transition score to next tag, only added if next timestep is valid (mask == 1)
            # shape: (batch_size,)
            score += self.transitions[tags[i - 1], tags[i]] * mask[i]

            # Emission score for next tag, only added if next timestep is valid (mask == 1)
            # shape: (batch_size,)
            score += emissions[i, torch.arange(batch_size), tags[i]] * mask[i]

        # End transition score
        # shape: (batch_size,)
        seq_ends = mask.long().sum(dim=0) - 1
        # shape: (batch_size,)
        last_tags = tags[seq_ends, torch.arange(batch_size)]
        # shape: (batch_size,)
        score += self.end_transitions[last_tags]

        return score

    def _compute_normalizer(
            self, emissions: torch.Tensor, mask: torch.ByteTensor) -> torch.Tensor:
        # emissions: (seq_length, batch_size, num_tags)
        # mask: (seq_length, batch_size)
        assert emissions.dim() == 3 and mask.dim() == 2
        assert emissions.shape[:2] == mask.shape
        assert emissions.size(2) == self.num_tags
        assert mask[0].all()

        seq_length = emissions.size(0)

        # Start transition score and first emission; score has size of
        # (batch_size, num_tags) where for each batch, the j-th column stores
        # the score that the first timestep has tag j
        # shape: (batch_size, num_tags)
        score = self.start_transitions + emissions[0]

        for i in range(1, seq_length):
            # Broadcast score for every possible next tag
            # shape: (batch_size, num_tags, 1)
            broadcast_score = score.unsqueeze(2)

            # Broadcast emission score for every possible current tag
            # shape: (batch_size, 1, num_tags)
            broadcast_emissions = emissions[i].unsqueeze(1)

            # Compute the score tensor of size (batch_size, num_tags, num_tags) where
            # for each sample, entry at row i and column j stores the sum of scores of all
            # possible tag sequences so far that end with transitioning from tag i to tag j
            # and emitting
            # shape: (batch_size, num_tags, num_tags)
            next_score = broadcast_score + self.transitions + broadcast_emissions

            # Sum over all possible current tags, but we're in score space, so a sum
            # becomes a log-sum-exp: for each sample, entry i stores the sum of scores of
            # all possible tag sequences so far, that end in tag i
            # shape: (batch_size, num_tags)
            next_score = torch.logsumexp(next_score, dim=1)

            # Set score to the next score if this timestep is valid (mask == 1)
            # shape: (batch_size, num_tags)
            score = torch.where(mask[i].unsqueeze(1), next_score, score)

        # End transition score
        # shape: (batch_size, num_tags)
        score += self.end_transitions

        # Sum (log-sum-exp) over all possible tags
        # shape: (batch_size,)
        return torch.logsumexp(score, dim=1)

    def _viterbi_decode(self, emissions: torch.FloatTensor,
                        mask: torch.ByteTensor) -> List[List[int]]:
        # emissions: (seq_length, batch_size, num_tags)
        # mask: (seq_length, batch_size)
        assert emissions.dim() == 3 and mask.dim() == 2
        assert emissions.shape[:2] == mask.shape
        assert emissions.size(2) == self.num_tags
        assert mask[0].all()

        seq_length, batch_size = mask.shape

        # Start transition and first emission
        # shape: (batch_size, num_tags)
        score = self.start_transitions + emissions[0]
        history = []

        # score is a tensor of size (batch_size, num_tags) where for every batch,
        # value at column j stores the score of the best tag sequence so far that ends
        # with tag j
        # history saves where the best tags candidate transitioned from; this is used
        # when we trace back the best tag sequence

        # Viterbi algorithm recursive case: we compute the score of the best tag sequence
        # for every possible next tag
        for i in range(1, seq_length):
            # Broadcast viterbi score for every possible next tag
            # shape: (batch_size, num_tags, 1)
            broadcast_score = score.unsqueeze(2)

            # Broadcast emission score for every possible current tag
            # shape: (batch_size, 1, num_tags)
            broadcast_emission = emissions[i].unsqueeze(1)

            # Compute the score tensor of size (batch_size, num_tags, num_tags) where
            # for each sample, entry at row i and column j stores the score of the best
            # tag sequence so far that ends with transitioning from tag i to tag j and emitting
            # shape: (batch_size, num_tags, num_tags)
            next_score = broadcast_score + self.transitions + broadcast_emission

            # Find the maximum score over all possible current tag
            # shape: (batch_size, num_tags)
            next_score, indices = next_score.max(dim=1)

            # Set score to the next score if this timestep is valid (mask == 1)
            # and save the index that produces the next score
            # shape: (batch_size, num_tags)
            score = torch.where(mask[i].unsqueeze(1), next_score, score)
            history.append(indices)

        # End transition score
        # shape: (batch_size, num_tags)
        score += self.end_transitions

        # Now, compute the best path for each sample

        # shape: (batch_size,)
        seq_ends = mask.long().sum(dim=0) - 1
        best_tags_list = []

        for idx in range(batch_size):
            # Find the tag which maximizes the score at the last timestep; this is our best tag
            # for the last timestep
            _, best_last_tag = score[idx].max(dim=0)
            best_tags = [best_last_tag.item()]

            # We trace back where the best last tag comes from, append that to our best tag
            # sequence, and trace it back again, and so on
            for hist in reversed(history[:seq_ends[idx]]):
                best_last_tag = hist[idx][best_tags[-1]]
                best_tags.append(best_last_tag.item())

            # Reverse the order because we start from the last timestep
            best_tags.reverse()
            best_tags_list.append(best_tags)

        return best_tags_list

import torch
import torch.nn as nn
# from torchcrf import CRF  # Assuming you are using a CRF implementation from a library like torchcrf

class POSCRFModel(nn.Module):
    def __init__(self, vocab_size, num_tags, embedding_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(num_embeddings=vocab_size, embedding_dim=embedding_dim)
        self.lstm = nn.LSTM(input_size=embedding_dim, hidden_size=hidden_dim, batch_first=True)
        self.hidden2tag = nn.Linear(hidden_dim, num_tags)
        self.crf = CRF(num_tags=num_tags, batch_first=True)

    def forward(self, sentences, tags=None, mask=None):
        embeds = self.embedding(sentences)
        lstm_out, _ = self.lstm(embeds)
        emissions = self.hidden2tag(lstm_out)
        # emissions = emissions.reshape(32,1000)
        # print(emissions.shape)

        if tags is not None:
            return -self.crf(emissions, tags, mask=mask)  # Return the negative log-likelihood
        else:
            return self.crf.decode(emissions, mask)  # Decode to get the tag sequence

# Example of initializing the model
# model = POSCRFModel(vocab_size=..., num_tags=..., embedding_dim=..., hidden_dim=...)

# Pseudocode for training loop
num_tags = 52
embedding_dim = 128
hidden_dim = 1024
vocab = len(set(word_to_idx.keys()))
num_epochs = 10
model = POSCRFModel(vocab, num_tags, embedding_dim, hidden_dim)
print(model)
optimizer = torch.optim.Adam(model.parameters())
print(optimizer)

def calculate_accuracy(pred_tags, true_tags, pad_index):
    correct = 0
    total = 0
    for pred, true in zip(pred_tags, true_tags):
        for p, t in zip(pred, true):
            if t != pad_index:  # Ignore padding
                correct += (p == t)
                total += 1
    return correct, total

total_correct=0
total_predictions=0

for epoch in range(num_epochs):
    print("Epoch",epoch)
    for sentences, tags in train_loader:
        # Forward pass
        emissions = model(sentences)
        emissions = torch.tensor(emissions)
        embeds = model.embedding(emissions)
        lstm_out, _ = model.lstm(embeds)
        emissions = model.hidden2tag(lstm_out)
        loss = -model.crf(emissions, tags)
        #print(loss)

        predicted_tags = model.crf.decode(emissions)

        # Calculate accuracy
        correct, total = calculate_accuracy(predicted_tags, tags.tolist(), tag_to_idx["<PAD>"])
        total_correct += correct
        total_predictions += total

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

epoch_accuracy = total_correct / total_predictions if total_predictions > 0 else 0
print(f'Accuracy of the training model is: {epoch_accuracy:.4f}')

with torch.no_grad():
    for sentences in test_loader:
        # Forward pass
        emissions = model(sentences)
        emissions = torch.tensor(emissions)
        embeds = model.embedding(emissions)
        lstm_out, _ = model.lstm(embeds)
        emissions = model.hidden2tag(lstm_out)
        #print(loss)
        predicted_tags = model.crf.decode(emissions)

        # Calculate accuracy
        correct, total = calculate_accuracy(predicted_tags, tags.tolist(), tag_to_idx["<PAD>"])
        total_correct += correct
        total_predictions += total

epoch_accuracy = total_correct / total_predictions if total_predictions > 0 else 0
print(f'Accuracy of the testing data{epoch_accuracy:.4f}')

print("The loss occured is", loss)
print(total_correct)
print(total_predictions)