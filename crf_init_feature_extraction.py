
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
