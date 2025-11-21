import logging
from abc import abstractmethod
from enum import StrEnum
from typing import BinaryIO, Iterable, Mapping

from .common import Scheme, Url, Header, Response
from ..exceptions import UnreachableCodeError, InvalidSchemeError
from ..mime.mimetype import MimeType
from ..net import SocketPool, Connection

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
                self.port = self._default_port()
        except InvalidSchemeError:
            raise
        except UnreachableCodeError:
            raise
        except Exception:
            raise ValueError(
                f'invalid URL: {url}, URL must be formatted as '
                f'"(http|https)://<host>(:<port>)?(/<path>)?"')

    def request(self) -> Response:
        conn = SocketPool().get_connection(self.host, self.port, self.secure)
        req_header = Header((
            ('Host', self.host),
            ('User-Agent', DEFAULT_USER_AGENT),
        ))
        res = self._request_http(conn, Method.GET, req_header)
        version, status, explanation = self._parse_http_version(res)
        res_header = self._parse_http_header(res)

        connection = res_header \
            .get_first_or_default('connection', 'keep-alive')
        if connection == 'keep-alive':
            content_len = int(res_header.get_first('content-length'))
            body = res.read(content_len)
        else:
            body = res.read()
            conn.close()

        content_type = res_header.get_first_or_default(
            'content-type', 'text/plain; charset=utf-8')

        return Response(
            status_code=int(status),
            content_type=MimeType(content_type),
            headers=res_header,
            body=body,
        )

    @property
    def secure(self) -> bool:
        return self.scheme == Scheme.HTTPS

    def _request_http(self, conn: Connection, method: Method,
                      header: Header) -> BinaryIO:
        req = '\r\n'.join((
            f'{method} {self.path} HTTP/{SUPPORTED_HTTP_VERSION}',
            *(f'{k}: {v}' for k, v in header.items()),
        )) + '\r\n\r\n'
        logging.debug('Request:\n%s', req)
        conn.send(req.encode())
        return conn.recv()

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return ()

    @staticmethod
    @abstractmethod
    def _default_port() -> int:
        pass

    @staticmethod
    def _parse_http_version(res: BinaryIO):
        status_line = res.readline()
        return status_line.split(b' ', 2)

    @classmethod
    def _parse_http_header(cls, res: BinaryIO):
        res_header = Header(header for header in cls._read_header_lines(res))

        assert 'transfer-encoding' not in res_header
        assert 'content-encoding' not in res_header

        return res_header

    @staticmethod
    def _read_header_lines(res: BinaryIO):
        while True:
            line = res.readline()
            if line == b'\r\n':
                break
            header, value = line.split(b':', 1)
            yield header.decode().casefold(), value.strip().decode()


class PlainHttpUrl(HttpUrl):
    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.HTTP,

    @staticmethod
    def _default_port():
        return 80


class HttpsUrl(HttpUrl):
    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.HTTPS,

    @staticmethod
    def _default_port():
        return 443
