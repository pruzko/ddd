import pandas as pd
import sqlite3


def load_df(table):
    with sqlite3.connect('../ddd/data/mail_dataset/spam_500.sqlite') as conn:
        return pd.read_sql(f'select * from {table}', conn)



def main():
    spam_gt = load_df('mails')
    spam_gt = spam_gt.rename(columns={'is_spam': 'is_spam_gt'})

    spam_gpt = load_df('gpt3')
    spam_gpt = spam_gpt.merge(spam_gt, on='id', how='left')
    spam_gpt = spam_gpt.dropna(subset=['is_spam'])

    total = len(spam_gpt)
    TP = ((spam_gpt['is_spam'] == 'yes') & (spam_gpt['is_spam_gt'] == 'yes')).sum()
    TN = ((spam_gpt['is_spam'] == 'no') & (spam_gpt['is_spam_gt'] == 'no')).sum()
    FP = ((spam_gpt['is_spam'] == 'yes') & (spam_gpt['is_spam_gt'] == 'no')).sum()
    FN = ((spam_gpt['is_spam'] == 'no') & (spam_gpt['is_spam_gt'] == 'yes')).sum()

    accuracy = (TP + TN) / total
    FPR = FP / (FP + TN)
    FNR = FN / (TP + FN)

    print(f'Total: {total}')
    print(f'Accuracy: {accuracy:.2f}')
    print(f'False Positive Rate (FPR): {FPR:.2f}')
    print(f'False Negative Rate (FNR): {FNR:.2f}')


if __name__ == '__main__':
    main()