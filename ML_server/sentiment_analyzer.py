import json

import google.generativeai as genai

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from tqdm import tqdm
from torch.utils.data import DataLoader

import torch
import torch.nn.functional as F
import re
import pandas as pd
import numpy as np
import requests
import zipfile
import os
import gc

def download_and_extract_data(url, csv_path):
    # ToDo: remove this
    # Check if the file already exists
    if os.path.isfile(csv_path):
        print(f"Found {csv_path}")
        data = pd.read_csv(csv_path)
        data.dropna(subset=['review_body'], inplace=True)
        data = data.sample(frac=1, random_state=42).reset_index(drop=True)
        return data

    # The testing dataset
    print("Downloading and extracting data...")

    response = requests.get(url)

    with open("temp", 'wb') as f:
        f.write(response.content)

    # Extract the contents
    with zipfile.ZipFile("temp", 'r') as zip_ref:
        zip_ref.extractall(".")

    # Load the testing dataset
    data = pd.read_csv(csv_path)

    # Drop empty reviews
    data.dropna(subset=['review_body'], inplace=True)

    # Shuffle the dataset
    data = data.sample(frac=1, random_state=42).reset_index(drop=True)

    # Review dataset info
    data.info()

    print("Data extraction complete.")

    # Remove the zip file
    os.remove("temp")

    return data

def preprocess_text(text):
    """
    Preprocess the input text by cleaning and normalizing it.
    """
    text = text.lower()  # Lowercase the text
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\d+', '', text)  # Remove digits
    text = text.strip()  # Remove leading/trailing whitespace
    return text

def batch_inference_sentiment_roberta(reviews, model, tokenizer, batch_size=32):
    # Preprocess and convert to list
    reviews = [preprocess_text(review) for review in reviews]

    # Tokenize the inputs
    inputs = tokenizer(reviews, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Create DataLoader for batching
    dataset = torch.utils.data.TensorDataset(inputs['input_ids'], inputs['attention_mask'])
    dataloader = DataLoader(dataset, batch_size=batch_size)

    all_predictions = []
    all_probs = []

    # Perform inference
    model.eval()
    with torch.no_grad():
        total_batches = len(dataloader)
        i = 0
        for batch in tqdm(dataloader, desc="Inferring sentiments..."):
            input_ids, attention_mask = batch
            outputs = model(input_ids, attention_mask=attention_mask)
            logits = outputs.logits

            # Get the predicted sentiment (0 = negative, 1 = positive)
            predictions = torch.argmax(logits, dim=-1)
            all_predictions.extend(predictions.cpu().numpy())

            # Convert to probabilities
            probs = F.softmax(logits, dim=-1)
            all_probs.extend(probs.cpu().numpy())

            # Yield progress
            yield json.dumps({"progress": int((i / total_batches) * 100)})
            i += 1

    # Yield the final result with predictions and probabilities
    yield json.dumps({
        'all_predictions': np.array(all_predictions).tolist(),
        'all_probs': np.array(all_probs).tolist()
    })

# Extract cons and pros from the top reviews
def get_pros_cons(reviews, n_top=10):
    """
    get pros and cons from the top n reviews based on ratings or helpfulness.

    Args:
    - reviews: List of dictionaries with 'title', 'text', 'rating', 'helpful' as keys.
    - n_top: Number of top reviews to summarize.

    Returns:
    - Summarized pros and cons.
    """
    # Sort reviews based on helpful votes or rating
    reviews_sorted = reviews.sort_values(by='helpful_votes')

    # Get the top n reviews
    top_reviews = reviews_sorted[:n_top]

    # Combine the review text from top reviews for summarization
    combined_text = " ".join([review['review_body'] for _, review in top_reviews.iterrows()])

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f' \
    {combined_text} \
    Extract pros and cons, and create a one-line summary from these reviews. \
    Be concise and ignore reviews that do not add pros and cons. \
    Format your response as {{"pros":[PROS1,PROS2,PROS3],"cons":[CONS1,CONS2,CONS3],"summary":SUMMARY}} \
    Do not add any other text except specified. Do not add any format specifiers\
   ')

    print("Summarized Review:", response.text)

    j_response = json.loads(response.text)

    return j_response['pros'], j_response['cons'], j_response['summary']

def analyze_sentiment(data):
    model_name = "siebert/sentiment-roberta-large-english"

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    # Enable FP16 inference if a GPU is available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    predicted_rating = None
    probs = None

    # Process the progress and final result
    for progress_update in batch_inference_sentiment_roberta(data['review_body'], model, tokenizer, batch_size=2):
        progress_data = json.loads(progress_update)

        if 'all_predictions' in progress_data:
            predicted_rating = np.array(progress_data['all_predictions'])  # Store the final result
            probs = np.array(progress_data['all_probs'])
        else:
            yield progress_update  # Yield progress if not final result

    # Process the result and attach predictions
    result = data[['review_body', 'helpful_votes']][:len(predicted_rating)].copy()
    result['predicted_rating'] = predicted_rating

    # Cleanup
    del data
    model.cpu()
    del model
    del tokenizer

    # Yield the final result
    yield json.dumps({'result': result.to_json(orient='records')})


def get_summary(description):
    return description

def cleanup():
    # Clear CUDA cache if GPU was used
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Explicitly call garbage collector
    gc.collect()

    print("Cleanup complete.")

if __name__ == '__main__':
    sentiment_result = analyze_sentiment()
    pros_cons = get_pros_cons(sentiment_result)

    cleanup()
