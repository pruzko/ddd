import asyncio

import ddd.utils as utils



class Mail:
    def __init__(
        self, id=None, service=None, address=None, receiver=None, receiver_name=None, sender=None, sender_name=None,
        datetime=None, subject=None, body=None, body_raw=None, links=[]
    ):
        self.id = id
        self.service = service
        self.address = address
        self.receiver = receiver
        self.receiver_name = receiver_name
        self.sender = sender
        self.sender_name = sender_name
        self.datetime = datetime
        self.subject = subject
        self.body = body
        self.body_raw = body_raw
        self.links = links


    def __repr__(self):
        return f'[{self.id}] {self.subject}'


    def to_dict(self):
        attrs = [
            'service', 'id', 'address', 'receiver', 'receiver_name', 'sender', 'sender_name', 'datetime', 'subject',
            'body', 'body_raw', 'links'
        ]
        return {a: getattr(self, a) for a in attrs}


    async def process_body(self):
        return await asyncio.wait_for(self._process_body(), timeout=3)


    async def _process_body(self):
        text = utils.extract_text_from_html(self.body_raw)
        text = utils.RE_LINKS.sub('<LINK>', text)
        text = utils.strip_css(text)
        text = utils.RE_LONG_STR.sub(' ', text)
        text = utils.RE_LONG_SEQ.sub(' ', text)
        text = utils.normalize_lines(text)
        self.body = text
        self.links = utils.extract_links_from_html(self.body_raw)