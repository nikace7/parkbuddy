import random
import json
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import spacy
from sklearn.metrics import accuracy_score

# Download spaCy model
#!python -m spacy download en_core_web_sm

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Load intents from JSON
with open('new_intents.json', 'r',encoding='utf-8') as file:
    intents = json.load(file)

# Initialize lists
words = []
classes = []
documents = []
ignoreLetters = ['?','!','.',',']

if 'intents' in intents:
    intent_list = intents['intents']
    for intent in intent_list:
        # Check if 'patterns' is in the current intent
        if 'patterns' in intent:
            for pattern in intent['patterns']:
                doc = nlp(pattern)
                
                # Extract tokens from the document
                tokens = [token.text for token in doc]
                
                # Filter out ignored characters and use the text of tokens
                wordList = []
                for token in doc:
                    if token.text not in ignoreLetters:
                        wordList.append(token.text)
                

               

                # Extend the words list with the text of tokens
                words.extend(wordList)
                
               

                
                # Append the document with lemmatized tokens and associated tag
                documents.append((wordList, intent['tag']))
                
                # Add the intent tag to classes if not already present
                if intent['tag'] not in classes:
                    classes.append(intent['tag'])

# Lemmatize words and remove duplicates
words = sorted(set(words))
classes = sorted(set(classes))

# Save processed data
pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl','wb'))

# Prepare training data
training = []
outputEmpty = [0] * len(classes)

for document in documents:
    bag = []
    wordPatterns = document[0]
    for word in words:
        bag.append(1) if word in wordPatterns else bag.append(0)
    
    outputRow = list(outputEmpty)
    outputRow[classes.index(document[1])] = 1
    training.append(bag + outputRow)

# Shuffle and convert to numpy array
random.shuffle(training)
training = np.array(training)

# Separate features and labels
trainX = training[:, :len(words)]
trainY = training[:, len(words):]

# Convert numpy arrays to PyTorch tensors
trainX = torch.tensor(trainX, dtype=torch.float32)
trainY = torch.tensor(trainY, dtype=torch.float32)
trainY = torch.argmax(trainY, axis=1)  # Convert to class indices

# Define the neural network model
class ChatbotModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(ChatbotModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)  # Adjust dropout rate
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.softmax(out)
        return out

# Initialize model, loss function, and optimizer
input_size = len(words)
hidden_size = 512
output_size = len(classes)
model = ChatbotModel(input_size, hidden_size, output_size)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0001)  # Adjust learning rate

# Training loop with early stopping
num_epochs = 20000
best_loss = float('inf')
patience = 1000  # Number of epochs to wait for improvement
early_stop_counter = 0

for epoch in range(num_epochs):
    model.train()
    outputs = model(trainX)
    loss = criterion(outputs, trainY)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if (epoch+1) % 50 == 0:
        print(f'Epoch [{epoch+1}/{num_epochs}], Loss: {loss.item():.4f}')

    # Early stopping
    if loss.item() < best_loss:
        best_loss = loss.item()
        early_stop_counter = 0
        torch.save(model.state_dict(), 'best_chatbotNep.pth')
    else:
        early_stop_counter += 1
    
    if early_stop_counter >= patience:
        print("Early stopping")
        break

print('Training completed')

# Load the best model for inference
model.load_state_dict(torch.load('best_chatbot.pth'))
torch.save(model.state_dict(), 'final_chatbot.pth')

# Now you can use `model` (best_chatbot.pth or final_chatbot.pth) for inference.
print('Training completed')
# Load the test intents from JSON
with open(r'C:\Users\khatr\OneDrive - Prime College\Desktop\Project\ParkBuddy\parkbuddy\chatbot_main\new_intents.json', 'r', encoding='utf-8') as file:
    test_intents = json.load(file)

# Initialize lists for test data
test_documents = []

# Prepare test data
if 'intents' in test_intents:
    intent_list = test_intents['intents']
    for intent in intent_list:
        if 'patterns' in intent:
            for pattern in intent['patterns']:
                doc = nlp(pattern)
                wordList = [token.text for token in doc if token.text not in ['?', '!', '.', ',']]
                
                # Append the document with tokens and associated tag
                test_documents.append((wordList, intent['tag']))

# Generate test data similar to the training data
test_data = []
outputEmpty = [0] * len(classes)

for document in test_documents:
    bag = []
    wordPatterns = document[0]
    for word in words:
        bag.append(1) if word in wordPatterns else bag.append(0)
    
    outputRow = list(outputEmpty)
    outputRow[classes.index(document[1])] = 1
    test_data.append(bag + outputRow)

# Convert test data to numpy array
test_data = np.array(test_data)

# Separate features and labels
testX = test_data[:, :len(words)]
testY = test_data[:, len(words):]

# Convert numpy arrays to PyTorch tensors
testX = torch.tensor(testX, dtype=torch.float32)
testY = torch.tensor(testY, dtype=torch.float32)
testY = torch.argmax(testY, axis=1)  # Convert to class indices

# Load the trained model
model = ChatbotModel(input_size=len(words), hidden_size=512, output_size=len(classes))
model.load_state_dict(torch.load('final_chatbot.pth'))

# Make predictions on the test data
model.eval()
with torch.no_grad():
    predictions = model(testX)
    predicted_classes = torch.argmax(predictions, axis=1)

# Calculate accuracy
accuracy = accuracy_score(testY, predicted_classes)
print(f"Model Accuracy on Test Data: {accuracy * 100:.2f}%")