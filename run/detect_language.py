import pandas as pd
import sqlite3
import tqdm

from langdetect import detect, LangDetectException


conn = sqlite3.connect('../ddd/data/mailinator.sqlite')
data = pd.read_sql('select * from mails', conn)
data = data.to_dict('records')


for d in tqdm.tqdm(data):
    s = d['subject'] if d['subject'] else ''
    s += ' '
    s += d['body'] if d['body'] else ''
    try:
        d['lang'] = detect(s)
    except LangDetectException:
        d['lang'] = None


data = pd.DataFrame(data)
data.to_sql('mails', conn, index=False, if_exists='replace')
