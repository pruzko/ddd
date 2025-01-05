import asyncio
import sqlite3

import aioboto3
from async_ip_rotator import IpRotator, ClientSession

from ddd import Mail
from ddd.providers import Mailinator



async def main():
    with open('../ddd/data/addresses.txt') as f:
        address = f.read().strip().split('\n')

    with open('../.env') as f:
        keys = f.read().strip().split('\n')[:2]
        aws_key_id, aws_key_secret = [k.split('=')[1] for k in keys]

    ip_rotator = IpRotator(
        target='https://www.mailinator.com',
        aws_key_id=aws_key_id,
        aws_key_secret=aws_key_secret,
        regions=['eu-central-1'],
    )

    aws_client = aioboto3.Session().client(
        service_name='lambda',
        region_name='eu-central-1',
        aws_access_key_id=aws_key_id,
        aws_secret_access_key=aws_key_secret,
    )

    with sqlite3.connect('../ddd/data/mailinator.sqlite') as conn:
        async with aws_client as aws_client:
            async with ip_rotator as ip_rotator:
                async with ClientSession(ip_rotator) as session:
                    provider = Mailinator(session, aws_client)
                    await provider.scrape(address, conn)




if __name__ == '__main__':
    asyncio.run(main())
