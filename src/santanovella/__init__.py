import json
import logging
import sys

logging.basicConfig(level=logging.DEBUG)

from . import html
from .protocol import http
from .protocol.common import Url, Response

MAX_REDIRECTION = 2


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: santanovella <url>')
        exit(1)

    url = Url.create_from(sys.argv[1])
    show_content_from(url)


def show_content_from(url):
    curr_url = url
    for _ in range(MAX_REDIRECTION + 1):
        res: Response = curr_url.request()
        print('# Response')
        print('## Header')
        res.headers.show()
        print('## Body')
        if res.content_type.type == 'text':
            if res.content_type.subtype == 'html':
                html.show(res.text)
            else:
                print(res.text)
        elif res.content_type.type == 'application':
            if res.content_type.subtype == 'json':
                print(json.dumps(res.json, indent=2))

        if not res.should_redirect:
            break

        curr_url = Url.create_from(res.redirect_path)
    else:
        logging.warning('redirected %d times, stopped' % MAX_REDIRECTION)
