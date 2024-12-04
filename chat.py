import random
import json
import torch
from nltk_utils import bag_of_words, tokenize
from model import NeuralNet

# Load intents file with error handling
try:
    with open('intents.json', 'r') as json_data:
        intents = json.load(json_data)
except FileNotFoundError:
    print("Error: intents.json file not found.")
    exit()
except json.JSONDecodeError:
    print("Error: Failed to parse intents.json file.")
    exit()

# Load trained model data with error handling
try:
    FILE = "data.pth"
    data = torch.load(FILE, weights_only=True)
except FileNotFoundError:
    print("Error: Pre-trained model file 'data.pth' not found.")
    exit()

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

# Initialize model and load state
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

def get_response(msg):
    sentence = tokenize(msg)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])  # Reshape for batch compatibility
    X = torch.from_numpy(X).float().to(device)  # Convert to tensor and move to the device

    with torch.no_grad():
        output = model(X)
        probs = torch.softmax(output, dim=1)
        _, predicted = torch.max(probs, dim=1)
        tag = tags[predicted.item()]

        prob = probs[0][predicted.item()]  # type: ignore

        # Debugging: Print the predicted tag and confidence
        #print(f"Predicted tag: {tag}, Probability: {prob.item()}")

        # Adjusted confidence threshold
        if prob.item() > 0.045:  # High confidence, valid response
            for intent in intents['intents']:
                if intent['tag'] == tag:
                    return random.choice(intent['responses'])
        elif prob.item() <= 0.029:  # Low confidence, fallback response
            return random.choice([
                "I'm sorry, I didn't quite understand that. Could you rephrase?",
                "Hmm, I'm not sure how to respond to that. Can you ask something else?",
                "I don't have an answer for that right now. Can I help with anything else?"
            ])
        else:
            # For medium confidence, fallback response
            return random.choice([
                "I'm sorry, I didn't quite understand that. Could you rephrase?",
                "Hmm, I'm not sure how to respond to that. Can you ask something else?",
                "I don't have an answer for that right now. Can I help with anything else?"
            ])
        
if __name__ == "__main__":
    print("Let's chat! (type 'quit' to exit)")
    while True:
        msg = input("You: ")
        if msg.lower() == "quit":
            break

        print(get_response(msg))
