import json
import os
import sqlite3

import faiss
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sentence_transformers import SentenceTransformer

from ddd.utils import DIR_DATA



app = Flask('Digital Dumpster Diver')

DB_PATH = os.path.join(DIR_DATA, 'mailinator.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['TEMPLATES_FOLDER'] = 'templates'

db = SQLAlchemy(app)
index = None
embeddings = None
model = None



class Mails(db.Model):
    id = db.Column(db.String, primary_key=True)
    service = db.Column(db.String)
    receiver = db.Column(db.String)
    sender = db.Column(db.String)
    sender_name = db.Column(db.String)
    datetime = db.Column(db.String)
    subject = db.Column(db.String)
    body = db.Column(db.String)
    body_raw = db.Column(db.String)
    links = db.Column(db.String)
    lang = db.Column(db.String)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mails')
def mails():
    try:
        page = int(request.args.get('page'))
    except:
        page = 0

    q = request.args.get('q')
    if not q:
        return render_template('mails.html', page=0, total=0)

    search_query = model.encode([q])
    D, I = index.search(x=search_query, k=len(embeddings))

    res = [(dist, idx) for dist, idx in zip(D[0], I[0]) if dist <= 1.3]

    s_idx = page * 10
    e_idx = s_idx + 10
    faiss_indices = [idx for _, idx in res[s_idx:e_idx]]
    mail_ids = embeddings['id'].iloc[faiss_indices].tolist()

    mails = (
        db.session.query(Mails)
        .filter(Mails.id.in_(mail_ids))
        .all()
    )
    for m in mails:
        m.links = json.loads(m.links)

    return render_template('mails.html', mails=mails, q=q, page=page, total=len(res))



if __name__ == '__main__':
    print('Loading embeddings...')
    with sqlite3.connect(DB_PATH) as conn:
        embeddings = pd.read_sql('select * from faiss_clean', conn)

    embeddings['embeddings'] = embeddings['embedding'].apply(lambda x: np.array(json.loads(x)))
    index_embeddings = np.stack(embeddings['embeddings'].values)

    index = faiss.IndexFlatL2(index_embeddings.shape[1])
    index.add(index_embeddings)

    print('Loading model...')
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print('Ready...')
    app.run(debug=True)
