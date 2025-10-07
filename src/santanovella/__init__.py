import logging
import sys

from . import html
from .protocol import http
from .protocol.common import Url


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) < 2:
        print('usage: santanovella <url>')
        exit(1)

    url = Url.create_from(sys.argv[1])
    header, body = url.request()
    print('# Response')
    print('## Header')
    http.show_headers(header)
    print('## Body')
    html.show(body)
