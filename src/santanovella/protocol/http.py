import logging
import socket
import ssl
from collections import defaultdict
from enum import StrEnum
from typing import TextIO, Optional, Mapping, Iterable

from .common import Scheme, Url
from ..exceptions import UnreachableCodeError, InvalidSchemeError

DEFAULT_USER_AGENT = f'Mozilla/5.0 (compatible; Santanovella/0.1.0)'
SUPPORTED_HTTP_VERSION = '1.1'


class Method(StrEnum):
    GET = 'GET'
    HEAD = 'HEAD'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    CONNECT = 'CONNECT'
    OPTIONS = 'OPTIONS'
    TRACE = 'TRACE'
    PATCH = 'PATCH'


class Header:
    _headers: defaultdict[str, list[str]]

    def __init__(self,
                 initial_values: Optional[Iterable[tuple[str, str]]] = None):
        self._headers = defaultdict(list[str])

        for header, values in initial_values:
            self._headers[header].append(values)

    def __str__(self):
        return str(self._headers)

    def __repr__(self):
        return repr(self._headers)

    def __contains__(self, item):
        return item in self._headers

    def add(self, key, value):
        self._headers[key].append(value)

    def get(self, key: str) -> list[str]:
        if key in self._headers:
            return self._headers[key]
        else:
            raise KeyError(key)

    def get_first(self, key: str):
        if key in self._headers and len(self._headers[key]) > 0:
            return self._headers[key][0]
        else:
            raise KeyError(key)

    def keys(self):
        return self._headers.keys()

    def items(self):
        for key, values in self._headers.items():
            for value in values:
                yield key, value


class HttpUrl(Url):
    scheme: Scheme
    host: str
    port: int
    path: str
    query_params: Mapping[str, str]

    def __init__(self, url: str):
        try:
            scheme, url = url.split('://')
            scheme = scheme.lower()

            if scheme not in self._allowed_schemes():
                raise InvalidSchemeError(scheme)

            self.scheme = Scheme(scheme)

            if '?' in url:
                url, query_params = url.split('?', maxsplit=1)

            if '/' in url:
                self.host, url = url.split('/', 1)
                self.path = f'/{url}'
            else:
                self.host = url
                self.path = '/'

            if ':' in self.host:
                self.host, port = self.host.split(':')
                self.port = int(port)
            else:
                if self.scheme == Scheme.HTTP:
                    self.port = 80
                elif self.scheme == Scheme.HTTPS:
                    self.port = 443
                else:
                    raise UnreachableCodeError()
        except InvalidSchemeError:
            raise
        except UnreachableCodeError:
            raise
        except Exception:
            raise ValueError(f'invalid HTTP(S) URL: {url}, URL must be formatted as "(http|https)://<host>(:<port>)?(/<path>)?"')

    def request(self):
        s = self._create_socket()
        s.connect((self.host, self.port))

        req_header = Header((
            ('Host', self.host),
            ('Connection', 'close'),
            ('User-Agent', DEFAULT_USER_AGENT),
        ))
        res = self._request_http(s, Method.GET, req_header)
        version, status, explanation = self._parse_http_version(res)
        res_header = self._parse_http_header(res)
        body = res.read()

        s.close()
        return res_header, body

    def _create_socket(self) -> socket.socket:
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        if self.scheme == Scheme.HTTPS:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        return s

    def _request_http(self, s: socket.socket, method: Method, header: Header) -> TextIO:
        req = '\r\n'.join((
            f'{method} {self.path} HTTP/{SUPPORTED_HTTP_VERSION}',
            *(f'{k}: {v}' for k, v in header.items()),
        )) + '\r\n\r\n'
        logging.debug('Request:\n%s', req)
        s.send(req.encode('utf-8'))
        res = s.makefile(
            mode='r',
            encoding='utf-8',
            newline='\r\n',
        )
        return res

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.HTTP, Scheme.HTTPS

    @staticmethod
    def _parse_http_version(res: TextIO):
        status_line = res.readline()
        return status_line.split(' ', 2)

    @classmethod
    def _parse_http_header(cls, res: TextIO):
        res_header = Header(header for header in cls._read_header_lines(res))

        assert 'transfer-encoding' not in res_header
        assert 'content-encoding' not in res_header

        return res_header

    @staticmethod
    def _read_header_lines(res: TextIO):
        while True:
            line = res.readline()
            if line == '\r\n':
                break
            header, value = line.split(':', 1)
            yield header.casefold(), value.strip()


def show_headers(header: Header):
    max_width = max(len(key) for key in header.keys())
    for key, value in header.items():
        print(f'{key:<{max_width}}: {value}')
