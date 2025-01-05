from elasticsearch import Elasticsearch
import pandas as pd
import sqlite3
import tqdm
import sys

es = Elasticsearch('http://localhost:9200')


def create_index():
    with sqlite3.connect('../ddd/data/mailinator.sqlite') as conn:
        data = pd.read_sql('select * from mails where lang="en"', conn)
        data = data[['id', 'sender', 'sender_name', 'subject', 'body']]
        data = data.to_dict('records')
        data = {d.pop('id'):d for d in data}

    for m_id, mail in tqdm.tqdm(data.items()): 
        res = es.index(index='mails', id=m_id, document=mail)


def search_mails(s):
    res = es.search(
        index='mails',
        size=10,
        query={
            'multi_match': {
                'query': s,
                'fields': ['sender', 'sender_name', 'subject', 'body'],
            }
        },
    )

    for d in res['hits']['hits']:
        print(f'{d["_id"]}\t{d["_source"]["subject"]}')
    print('Total:', res['hits']['total']['value'])



if __name__ == '__main__':
    search_mails(sys.argv[1])
