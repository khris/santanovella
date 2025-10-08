import json
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
    print('# Response')
    print('## Header')
    res.headers.show()
    print('## Body')
    if res.content_type.type == 'text':
        if res.content_type.subtype == 'html':
            html.show(res.text)
        else:
            print(res.text)
    if res.content_type.type == 'application':
        if res.content_type.subtype == 'json':
            print(json.dumps(res.json, indent=2))
