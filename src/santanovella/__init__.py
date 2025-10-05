import sys

from . import http, html


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: santanovella <url>')
        exit(1)

    url = http.URL(sys.argv[1])
    header, body = url.request()
    print('# Response')
    print('## Header')
    http.show_headers(header)
    print('## Body')
    html.show(body)
