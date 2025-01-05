import asyncio
import datetime as dt
import email
import email.policy
import email.utils
import itertools
import json
import tqdm

import pandas as pd

from ddd import Mail
from ddd.utils import chunks



class Mailinator:
    def __init__(self, session, aws_client):
        self.session = session
        self.aws_client = aws_client
        self._lambda_idx = itertools.cycle(range(100))


    async def scrape(self, addresses, conn):
        scrape_ts = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for addr_chunk in tqdm.tqdm(list(chunks(addresses, 20))):
            try:
                m_ids = await self.fetch_mailboxes(addr_chunk)
            except Exception as e:
                tqdm.tqdm.write(f'Error Chunk: {e}, {addr_chunk}')

            mails = [Mail(
                id=m_id,
                service='mailinator',
                address=addr,
            ) for addr, m_ids in m_ids.items() for m_id in m_ids if not self._mail_exists(m_id, conn)]
            
            for idx, m in enumerate(mails, 1):
                try:
                    await self.fetch_mail_content(m)
                    tqdm.tqdm.write(f'({idx} / {len(mails)}) {m}')
                except Exception as e:
                    tqdm.tqdm.write(f'Error: {e}')
                finally:
                    await asyncio.sleep(0.1)

            mails = [mail.to_dict() for mail in mails]
            for m in mails:
                m['links'] = None if m['links'] is None else json.dumps(m['links'])
                m['scrape_ts'] = scrape_ts

            mails = pd.DataFrame(mails)
            mails = mails.applymap(lambda x: x.encode('utf-8', 'ignore').decode('utf-8') if isinstance(x, str) else x)
            mails.to_sql('mails', conn, index=False, if_exists='append')


    @staticmethod
    def _mail_exists(m_id, conn):
        curs = conn.cursor()
        try:
            curs.execute('SELECT 1 FROM mails WHERE id=? LIMIT 1;', [m_id])
            return bool(curs.fetchone())
        except:
            return False
        finally:
            curs.close()


    async def fetch_mailboxes(self, addresses):
        assert len(addresses) <= 20, 'Mailinator will not provide that many addresses at once, make several calls instead.'

        res = await self.aws_client.invoke(
            FunctionName=f'DDD_mailinator_mailboxes_{next(self._lambda_idx)}',
            Payload=json.dumps({'addresses': addresses})
        )
        res = await res['Payload'].read()
        res = json.loads(res)

        assert res['status'] == 200, f'Unexpected status code: {res["status"]}'
        return res['mails']


    async def fetch_mail_content(self, mail):
        res = await self.session.get(f'/fetch_public?format=raw&msgid={mail.id}', cookies={})
        assert res.status == 200, f'Unexpected status code: {res.status}'

        data = await res.text()
        data = json.loads(data)['data']
        assert type(data) is str, f'Unexpected mail data: {str(data)[:20]}... '

        mail_data = email.message_from_string(data, policy=email.policy.default)

        mail.receiver_name, mail.receiver = email.utils.parseaddr(mail_data['to'])
        mail.sender_name, mail.sender = email.utils.parseaddr(mail_data['from'])
        mail.receiver_name = mail.receiver_name if mail.receiver_name else None
        mail.sender_name = mail.sender_name if mail.sender_name else None
        mail.subject = mail_data['subject']
        try:
            mail.datetime = email.utils.parsedate_to_datetime(mail_data['date'])
            mail.datetime = mail.datetime.strftime('%Y-%m-%d %H:%M:%S')
        except:
            mail.datetime = None

        body_data = mail_data.get_body(['html', 'plain'])
        if not body_data:
            mail.body_raw = None
            mail.body = None
        else:
            mail.body_raw = body_data.get_content()
            await mail.process_body()
