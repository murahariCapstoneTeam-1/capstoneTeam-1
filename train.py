import numpy as np
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from nltk_utils import bag_of_words, tokenize, stem
from model import NeuralNet
from torch.optim.adam import Adam

# Load intents file
with open('intents.json', 'r') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

# Loop through each sentence in our intents patterns
for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))

# Stem and lower each word
ignore_words = ['?', '.', '!']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words = sorted(set(all_words))
tags = sorted(set(tags))

print(f'{len(xy)} patterns')
print(f'{len(tags)} tags:', tags)
print(f'{len(all_words)} unique stemmed words:', all_words)

# Create training data
X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    label = tags.index(tag)
    y_train.append(label)

X_train = np.array(X_train)
y_train = np.array(y_train)

# Hyper-parameters 
num_epochs = 10000  # You can adjust this value to 100,000 or higher as needed
batch_size = 8
learning_rate = 0.01  # Reduced learning rate
input_size = len(X_train[0])
hidden_size = 32  # Increased hidden layer size
output_size = len(tags)
print(f'Input size: {input_size}, Output size: {output_size}')

# Dataset and DataLoader
class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

dataset = ChatDataset()
train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True, num_workers=0)

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Model, loss function, and optimizer
model = NeuralNet(input_size, hidden_size, output_size).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = Adam(model.parameters(), lr=learning_rate)

# Training loop with early stopping based on patience
prev_loss = None
patience = 5  # Number of epochs without improvement before stopping
epochs_without_improvement = 0
print_every = 100  # Print loss every 100 epochs
early_stopping_triggered = False  # Prevent multiple prints

for epoch in range(num_epochs):
    total_loss = 0
    for (words, labels) in train_loader:
        words = words.to(device)
        labels = labels.to(dtype=torch.long).to(device)
        
        # Forward pass
        outputs = model(words)
        loss = criterion(outputs, labels)
        
        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    avg_loss = total_loss / len(train_loader)

    # Print every `print_every` epochs
    if epoch % print_every == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.4f}')

    if prev_loss is not None and avg_loss > prev_loss:
        epochs_without_improvement += 1
        if epochs_without_improvement >= patience and not early_stopping_triggered:
            print("Early stopping triggered due to no improvement.")
            early_stopping_triggered = True  # Prevent repeated messages
            break
    else:
        epochs_without_improvement = 0  # Reset counter if loss improves

    prev_loss = avg_loss

print(f'Final loss: {avg_loss:.4f}')

# Save the trained model
data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

FILE = "data.pth"
torch.save(data, FILE)

print(f'Training complete. File saved to {FILE}')
