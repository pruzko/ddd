import asyncio
import code
import json
import os
import socket
import urllib.parse

import aioboto3
import tqdm
from aiohttp_socks import ProxyConnector
from async_ip_rotator import ClientSession, IpRotator
from bs4 import BeautifulSoup

from ddd.utils import DIR_ROOT, DIR_DATA, chunks
from ddd.providers import Mailinator



async def trigger_email(ip_rotator, addr):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.120 Safari/537.36',
    }
    async with ClientSession(rotator=ip_rotator, headers=headers) as sess:
        res = await sess.get('https://id.atlassian.com/login/resetpassword')

        res = await sess.post(
            url=f'https://id.atlassian.com/rest/resetpassword?email={urllib.parse.quote_plus(addr)}',
            json={'email': addr},
        )
        text = await res.text()
        assert json.loads(text)['isSuccessful'], 'Something went wrong'


async def check_accounts(mailinator, addresses):
    res = {}

    mailboxes = await mailinator.fetch_mailboxes(addresses)
    for addr, mails in mailboxes.items():
        if any(['atlassian' in m.get('subject', '').lower() for m in mails]):
            res[addr] = True
        else:
            res[addr] = False

    return res


def load_addresses():
    with open(os.path.join(DIR_DATA, 'addresses.txt')) as f:
        return [addr for addr in f.read().strip().split('\n')]


def load_aws_credentials():
    with open(os.path.join(DIR_ROOT, '..', '.env')) as f:
        keys = f.read().strip().split('\n')[:2]
        return [k.split('=')[1] for k in keys]



async def main():
    aws_key_id, aws_key_secret = load_aws_credentials()
    addresses = load_addresses()
    data = {addr: None for addr in addresses}

    aws_client = aioboto3.Session().client(
        service_name='lambda',
        region_name='eu-central-1',
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_key_secret,
    )

    ip_rotator = IpRotator(
        target='https://id.atlassian.com',
        aws_key_id=aws_key_id,
        aws_key_secret=aws_key_secret,
        regions=['eu-central-1']
    )

    async with ip_rotator as ip_rotator, aws_client as aws_client:
        mailinator = Mailinator(session=None, aws_client=aws_client)

        with tqdm.tqdm(total=len(addresses)) as pbar:
            for addr_chunk in chunks(addresses, 10):
                try:
                    for addr in addr_chunk:
                        await trigger_email(ip_rotator, f'{addr}@mailinator.com')
                        await asyncio.sleep(1)

                    await asyncio.sleep(3)
                    results = await check_accounts(mailinator, addr_chunk)
                    data = data | results

                    for addr, res in results.items():
                        if res:
                            tqdm.tqdm.write(f'{addr}: \033[92mHIT\033[0m')
                        else:
                            tqdm.tqdm.write(f'{addr}: \033[91mMISS\033[0m')
                    pbar.update(len(addr_chunk))
                except Exception as e:
                    raise e
                    tqdm.tqdm.write(f'Error: {e}')
                finally:
                    await asyncio.sleep(2)

    try:
        with open('atlassian_results.json', 'w') as f:
            json.dump(data, f, indent=4)
    except:
        code.interact(local=locals()|globals())


if __name__ == '__main__':
    asyncio.run(main())
