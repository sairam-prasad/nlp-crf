# -*- coding: utf-8 -*-
"""crf_init

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Tumaj_AwlAC9KBWMCdyisITjKTpY1lFY
"""

!pip install -qq datasets conllu

from datasets import load_dataset

# Load the Universal Dependencies dataset for POS tagging
# The dataset name and subset would depend on the specific version you want to use
# For example, to load the English-EWT (English Web Treebank) dataset:
dataset = load_dataset('universal_dependencies', 'en_ewt')

# The dataset is now a Hugging Face DatasetDict object, which has train, validation, and test splits
# You can access the data like this:
train_data = dataset['train']
validation_data = dataset['validation']
test_data = dataset['test']

# Let's implement the feature extraction function
def feature_extraction(token, pos_tag, prev_token=None, next_token=None):
    features = {
        'word.lower': token.lower(),
        'word[-3:]': token[-3:],
        'word[-2:]': token[-2:],
        'word.isupper': token.isupper(),
        'word.istitle': token.istitle(),
        'word.isdigit': token.isdigit(),
        'pos': pos_tag, # POS tag itself can be a useful feature
        'prev_word': '' if prev_token is None else prev_token.lower(),
        'next_word': '' if next_token is None else next_token.lower(),
        # Additional features can be added here
    }
    return features

# Function to process the dataset and extract features
def preprocess_dataset(dataset_split):
    features = []
    labels = []
    for sentence in dataset_split:
        tokens = sentence['tokens']
        pos_tags = sentence['upos']
        for i in range(len(tokens)):
            token = tokens[i]
            pos_tag = pos_tags[i]
            prev_token = tokens[i-1] if i > 0 else None
            next_token = tokens[i+1] if i < len(tokens)-1 else None
            token_features = feature_extraction(token, pos_tag, prev_token, next_token)
            features.append(token_features)
            labels.append(pos_tag)
    return features, labels

# Extract features and labels from the training data
train_features, train_labels = preprocess_dataset(train_data)

# Now 'train_features' contains the features for each token in the training set
# and 'train_labels' contains the corresponding POS tags


