import random
import json
import pickle
import numpy as np
import torch
import torch.nn as nn
import spacy
import webbrowser
import os
import json

# Get the directory where jec_chatbot.py is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Create an absolute path to new_intents.json
intents_path = os.path.join(base_dir, 'new_intents.json')

# Load the intents from the JSON file
with open(intents_path, 'r') as file:
    intents = json.load(file)

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Load intents and preprocessing data   
intents = json.loads(open(r'C:\Users\khatr\OneDrive - Prime College\Desktop\Project\ParkBuddy\parkbuddy\chatbot_main\new_intents.json').read())
words = pickle.load(open(r'C:\Users\khatr\OneDrive - Prime College\Desktop\Project\ParkBuddy\parkbuddy\chatbot_main\words.pkl', 'rb'))
classes = pickle.load(open(r'C:\Users\khatr\OneDrive - Prime College\Desktop\Project\ParkBuddy\parkbuddy\chatbot_main\classes.pkl', 'rb'))

# Define and load the PyTorch model
class ChatbotModel(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super(ChatbotModel, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.5)
        self.fc2 = nn.Linear(hidden_size, output_size)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.softmax(out)
        return out

# Modify path to your trained PyTorch model file
model_path = r'C:\Users\khatr\OneDrive - Prime College\Desktop\Project\ParkBuddy\parkbuddy\chatbot_main\best_chatbotNep.pth'
model = ChatbotModel(input_size=len(words), hidden_size=512, output_size=len(classes))
model.load_state_dict(torch.load(model_path))
model.eval()

def clean_up_sentence(sentence):
    doc = nlp(sentence)
    sentence_words = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
    return sentence_words

def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        if w in words:
            bag[words.index(w)] = 1
    return np.array(bag)

def predict_class(sentence):
    bow = bag_of_words(sentence)
    bow_tensor = torch.from_numpy(bow).float().unsqueeze(0)
    outputs = model(bow_tensor)
    _, predicted = torch.max(outputs, 1)
    predicted_class = classes[predicted.item()]
    return predicted_class

def get_response(predicted_intent, intents):
    response = None  # Initialize the response variable
    
    for intent in intents['intents']:
        if intent['tag'] == predicted_intent:
            response = random.choice(intent['responses'])
            break  # Exit the loop once we find the match

    # If no response was found, provide a fallback message
    if response is None:
        response = "Sorry, I don't understand that. Can you rephrase?"

    return response
def contains_link(response):
    # A simple check for 'http' or 'https' in the response
    if 'http' in response or 'https' in response:
        return True
    return False

def extract_link(response):
    # Extract the link from the response (assuming the link is enclosed in <>)
    start_index = response.find('<')
    end_index = response.find('>')
    if start_index != -1 and end_index != -1:
        return response[start_index + 1:end_index]
    return None

def ask_for_confirmation(link):
    while True:
        user_input = input(f"Do you want to go to this link? (yes/no): ").strip().lower()
        if user_input in ["yes", "no"]:
            return user_input == "yes"

# Loading the transformer models for speech synthesis
print("GO! Bot is running!")

# def chatbot_response(user_input):
#     predicted_intent = predict_class(user_input)
#     response = get_response(predicted_intent, intents)
#     return response

while True:
    message = input("User: ")
    predicted_intent = predict_class(message)
    response = get_response(predicted_intent, intents)
    print(f"Bot:{response}\n")

    if contains_link(response):
        link = extract_link(response)
        if link and ask_for_confirmation(link):
            webbrowser.open(link)
            continue