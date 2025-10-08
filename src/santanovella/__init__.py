import logging
import sys

from . import html
from .protocol import http
from .protocol.common import Url, Response


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        print('usage: santanovella <url>')
        exit(1)

    url = Url.create_from(sys.argv[1])
    res: Response = url.request()
    if url.scheme in ('http', 'https'):
        print('# Response')
        print('## Header')
        res.headers.show()
        print('## Body')
        html.show(res.text)
    elif url.scheme == 'file':
        print(f'# {url.path}')
        print(res.text)
    elif url.scheme == 'data':
        print('# Data')
        print(res.text)
