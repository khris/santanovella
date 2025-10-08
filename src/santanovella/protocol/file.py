from os import PathLike
from pathlib import Path
from typing import Iterable

from .common import Scheme, Url, Response
from ..exceptions import InvalidSchemeError
from ..mime.mimetype import MimeType


class FileUrl(Url):
    scheme: Scheme
    host: str
    path: PathLike

    def __init__(self, url: str):
        scheme, url = url.split('://')
        scheme = scheme.lower()

        if scheme not in self._allowed_schemes():
            raise InvalidSchemeError(scheme)

        self.scheme = Scheme(scheme)

        if url.startswith('/'):
            self.host = 'localhost'
            self.path = Path(url)
        else:
            self.host, path = url.split('/', 1)
            self.path = Path(path)

    def request(self) -> Response:
        if self.host != 'localhost':
            raise NotImplementedError('access to a non-local file resources '
                                      'is not supported yet')

        with open(self.path, 'rb') as f:
            return Response(
                content_type=MimeType('text/plain; charset=utf-8'),
                body = f.read(),
            )

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.FILE,
