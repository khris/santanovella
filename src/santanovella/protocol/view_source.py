import base64
from typing import Iterable

from .common import Scheme, Url, Response, Header
from ..exceptions import InvalidSchemeError
from ..mime.mimetype import MimeType


class ViewSourceUrl(Url):
    scheme: Scheme
    nested_url: Url

    def __init__(self, url: str):
        scheme, nested_url = url.split(':', 1)
        scheme = scheme.lower()

        if scheme not in self._allowed_schemes():
            raise InvalidSchemeError(scheme)

        self.scheme = Scheme(scheme)
        self.nested_url = Url.create_from(nested_url)

    def request(self) -> Response:
        orig_res = self.nested_url.request()
        try:
            charset = orig_res.content_type.charset
        except ValueError:
            charset = 'utf-8'

        orig_res.content_type = MimeType(f'text/plain; charset={charset}')
        return orig_res

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.VIEW_SOURCE,
