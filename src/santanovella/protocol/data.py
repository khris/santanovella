import base64
from typing import Iterable

from .common import Scheme, Url, Response, Header
from ..exceptions import InvalidSchemeError
from ..mime.mimetype import MimeType


class DataUrl(Url):
    scheme: Scheme
    mimetype: MimeType = MimeType('text/plain;charset=US-ASCII')
    data: bytes

    def __init__(self, url: str):
        scheme, data = url.split(':', 1)
        scheme = scheme.lower()

        if scheme not in Scheme:
            raise InvalidSchemeError(scheme)

        self.scheme = Scheme(scheme)

        comma_pos = data.find(',')

        if comma_pos == -1 or comma_pos == len(data) - 1:
            raise ValueError(f'"data" URI should be '
                             f'"data:[<mediatype>][;base64],<data>", '
                             f'but it\'s not: "{url}"')

        is_base64 = False
        if comma_pos > 0:
            last_semicolon_pos = data[:comma_pos].rfind(';')
            is_base64 = (last_semicolon_pos != -1 and
                      data[last_semicolon_pos + 1:comma_pos] == 'base64')
            if is_base64:
                self.mimetype = MimeType(data[:last_semicolon_pos])
            else:
                self.mimetype = MimeType(data[:comma_pos])

        self.data = data[comma_pos + 1:].encode()

        if is_base64:
            self.data = base64.urlsafe_b64decode(self.data)

    def request(self) -> Response:
        return Response(
            status_code=200,
            content_type=self.mimetype,
            body=self.data,
        )

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.DATA,
