from . import http


def main() -> None:
    url = http.URL('http://google.com')
    header, body = url.request()
    print(header)
    print(body)
