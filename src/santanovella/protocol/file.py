from os import PathLike
from pathlib import Path
from typing import Iterable

from .common import Scheme, Url
from ..exceptions import InvalidSchemeError


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

    def request(self):
        if self.host != 'localhost':
            raise NotImplementedError("access to a non-local file resources is not supported yet")

        with open(self.path) as f:
            return f.read()

    @classmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        return Scheme.FILE,
