

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

# schema
print(train_data)

train_data[i]['idx']

for i in range(len(train_data[:5])):
  print('\n\n\nsample',i)
  for sample in train_data[0]:
    print(train_data[i][sample])

for i in range(len(validation_data[:5])):
  print('\n\n\nsample',i)
  for sample in validation_data[0]:
    print(validation_data[i][sample])

for i in range(len(test_data[:5])):
  print('\n\n\nsample',i)
  for sample in test_data[0]:
    print(test_data[i][sample])

