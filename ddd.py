import asyncio
import pickle as pkl
import sys
from tqdm import tqdm
from datetime import datetime as dt

from ddd.scrapers import Mailinator
from ddd.utils import DIR_MAIL_DATASET, load_address_list



async def main():
    address_list = load_address_list()
    address_list = address_list[58:]

    scrp = Mailinator()
    await scrp.init()

    mails = []
    for i, address in enumerate(tqdm(address_list), 1):
        try:
            tqdm.write(f'Scraping ({i}/{len(address_list)}) addr: {address}')
            mailbox = await scrp.scrape_mail_box(address)
            await asyncio.sleep(1)

            for i, mail in enumerate(mailbox, 1):
                try:
                    mail = await scrp.scrape_mail(mail.receiver, mail.id)
                    mails.append(mail)
                    tqdm.write(f'({i}/{len(mailbox)}) {mail}, total: {len(mails)}')
                    await asyncio.sleep(0.1)

                except Exception as e:
                    tqdm.write(f'Error ({mail.id}): {e}')
                    await asyncio.sleep(1)

        except Exception as e:
            tqdm.write(f'Error ({address}): {e}')
            await asyncio.sleep(1)

    with open(f'{DIR_MAIL_DATASET}/mails_{dt.now().strftime("%Y-%m-%d_%H:%M")}.pkl', 'wb') as f:
        pkl.dump(mails, f)

    import code; code.interact(local=locals() | globals())

    await scrp.close()


if __name__ == '__main__':
    asyncio.run(main())