from flask import Flask, request, jsonify
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import os

app = Flask(__name__)
MODEL_DIR = './sentiment_model'

try:
    tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
    model = BertForSequenceClassification.from_pretrained(MODEL_DIR)
except Exception as e:
    print(f"CRITICAL ERROR: Could not load model from {os.path.abspath(MODEL_DIR)}")
    raise e

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data or 'tweet' not in data:
            return jsonify({'error': 'No tweet provided. Send JSON with a "tweet" key.'}), 400
        
        tweet = data['tweet']
        inputs = tokenizer(tweet, return_tensors="pt", truncation=True, max_length=128)
        
        with torch.no_grad():
            outputs = model(**inputs)
            prediction = torch.argmax(outputs.logits, dim=-1).item()
            
        sentiment_map = {0: 'Negative', 1: 'Neutral', 2: 'Positive'}
        return jsonify({'tweet': tweet, 'sentiment': sentiment_map.get(prediction, "Unknown")}), 200
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)