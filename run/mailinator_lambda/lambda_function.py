import json
import asyncio

import aiohttp



loop = asyncio.new_event_loop()


async def fetch_mailboxes(addresses):
    mailboxes = {}

    async with aiohttp.ClientSession() as sess:
        res = await sess.get(f'https://mailinator.com/v4/public/inboxes.jsp')
        assert res.status == 200, f'Unexpected status code: {res.status}'

        async with sess.ws_connect('wss://mailinator.com/ws/fetchpublic') as ws:
            for addr in addresses:
                try:
                    msg = { 'cmd': 'sub', 'channel': addr }
                    await ws.send_str(json.dumps(msg, separators=list(',:')))

                    while True:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if 'msgs' in data:
                                mailboxes[addr] = [{
                                    'id': m.get('id'),
                                    'from': m.get('fromfull'),
                                    'subject': m.get('subject'),
                                } for m in data['msgs']]
                                break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            raise ws.exception() if ws.exception() else Exception('WS closed with no exception')
                except Exception as e:
                    mailboxes[addr] = None
                finally:
                    await asyncio.sleep(0.1)

    return mailboxes


async def _lambda_handler(event, context):
    try:
        mailboxes = await fetch_mailboxes(event['addresses'])
        return {
            'status': 200,
            'mails': mailboxes,
        }
    except Exception as e:
        return {
            'status': 500,
            'error': str(e),
        }


def lambda_handler(event, context):
    global loop
    if loop.is_closed():
        loop = asyncio.new_event_loop()
    return loop.run_until_complete(_lambda_handler(event, context))
