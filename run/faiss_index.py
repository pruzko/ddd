import json
import re
import sqlite3
import sys
import tqdm

import pandas as pd
from sentence_transformers import SentenceTransformer



tqdm.tqdm.write('Loading model...')
model = SentenceTransformer('all-MiniLM-L6-v2')


def preprocess_text(text):
    text = text if text else ''
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    return text


def create_embeddings():
    tqdm.tqdm.write('Reading mails...')
    with sqlite3.connect('../ddd/data/mailinator.sqlite') as conn:
        data = pd.read_sql('select * from mails where lang="en"', conn)

    tqdm.tqdm.write('Preprocessing...')
    data = data[['id', 'subject', 'body']]
    data['subject'] = data['subject'].apply(preprocess_text)
    data['body'] = data['body'].apply(preprocess_text)

    tqdm.tqdm.write('Embedding...')
    tqdm.tqdm.pandas()
    data['embedding'] = data['subject'] + '\n' + data['body']
    data['embedding'] = data['embedding'].progress_apply(lambda x: model.encode(x).tolist())

    data = data[['id', 'embedding']]
    data['embedding'] = data['embedding'].apply(lambda x: json.dumps(x))
    with sqlite3.connect('../ddd/data/mailinator.sqlite') as conn:
        data.to_sql('faiss', conn, if_exists='replace', index=False)



import faiss
import code
import numpy as np

if __name__ == '__main__':
    with sqlite3.connect('../ddd/data/mailinator.sqlite') as conn:
        data = pd.read_sql('select * from faiss', conn)

    embeddings = data['embedding'].apply(lambda x: np.array(json.loads(x)))
    embeddings = np.stack(embeddings.values)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)


    search_query = model.encode(['facebook account password'])

    D, I = index.search(search_query=search_query, k=embeddings.shape[0])

    code.interact(local=locals()|globals())
