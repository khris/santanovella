import socket
import ssl
from collections import defaultdict
from enum import StrEnum
from typing import TextIO, Iterable, Optional

from .exceptions import UnreachableCodeException


class Scheme(StrEnum):
    HTTP = "http"
    HTTPS = "https"


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


class URL:
    def __init__(self, url: str):
        try:
            self.scheme, url = url.split('://')
            assert self.scheme in Scheme

            if not url.endswith('/'):
                url += '/'

            self.host, url = url.split('/', 1)
            self.path = f'/{url}'

            if ':' in self.host:
                self.host, port = self.host.split(':')
                self.port = int(port)
            else:
                if self.scheme == Scheme.HTTP:
                    self.port = 80
                elif self.scheme == Scheme.HTTPS:
                    self.port = 443
                else:
                    raise UnreachableCodeException()
        except AssertionError:
            raise NotImplementedError(t'{self.scheme} is not supported by santanovella yet')
        except Exception:
            raise ValueError(t'invalid URL: {url}, URL must be formatted as "<scheme>://<host>(:<port>)?(/<path>)?"')

    def request(self):
        s = self._create_socket()
        s.connect((self.host, self.port))

        res = self._request_http(s)
        version, status, explanation = self._parse_http_version(res)
        res_header = URL._parse_http_header(res)
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

    def _request_http(self, s: socket.socket) -> TextIO:
        req = (f'GET {self.path} HTTP/1.0\r\n'
               f'Host: {self.host}\r\n'
               f'\r\n')
        s.send(req.encode('utf-8'))
        res = s.makefile(
            mode='r',
            encoding='utf-8',
            newline='\r\n',
        )
        return res

    @staticmethod
    def _parse_http_version(res: TextIO):
        status_line = res.readline()
        return status_line.split(' ', 2)

    @staticmethod
    def _parse_http_header(res: TextIO):
        res_header = Header(header for header in URL._read_header_lines(res))

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
