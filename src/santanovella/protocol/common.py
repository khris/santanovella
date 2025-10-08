import json
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from enum import StrEnum, auto
from typing import ClassVar, MutableMapping, Iterable, Optional

from santanovella.exceptions import InvalidSchemeError
from santanovella.mime.mimetype import MimeType


class Scheme(StrEnum):
    HTTP = auto()
    HTTPS = auto()
    FILE = auto()
    DATA = auto()
    VIEW_SOURCE = "view-source"


class Header:
    _headers: defaultdict[str, list[str]]

    def __init__(self,
                 initial_values: Optional[Iterable[tuple[str, str]]] = None):
        self._headers = defaultdict(list[str])

        if initial_values is None:
            return

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
        try:
            return self._headers[key.lower()]
        except KeyError:
            raise KeyError(f'header does not have key "{key}"')

    def get_or_default(self, key: str, default=None) -> list[str]:
        try:
            return self.get(key)
        except KeyError:
            return default if default is not None else []

    def get_first(self, key: str) -> str:
        try:
            return self._headers[key.lower()][0]
        except (KeyError, IndexError):
            raise KeyError(f'header does not have key "{key}"')

    def get_first_or_default(self, key: str, default=None) -> str:
        try:
            return self.get_first(key)
        except KeyError:
            return default

    def keys(self):
        return self._headers.keys()

    def items(self):
        for key, values in self._headers.items():
            for value in values:
                yield key, value

    def show(self):
        if not self._headers:
            return

        max_width = max(len(key) for key in self.keys())
        for key, value in self.items():
            print(f'{key:<{max_width}}: {value}')


class Response:
    status_code: int
    content_type: MimeType
    headers: Header
    body: bytes

    def __init__(self, /,
                 status_code: int = 200,
                 content_type: Optional[MimeType] = None,
                 headers: Optional[Header] = None,
                 body: Optional[bytes] = None,
                 ):
        self.status_code = status_code
        self.headers = headers or Header()
        self.body = body or b''
        self.content_type = content_type \
                            or MimeType('text/plain; charset=utf-8')

    @property
    def json(self):
        return json.loads(self.body)

    @property
    def text(self):
        return self.body.decode(self.content_type.charset)


class Url(metaclass=ABCMeta):
    subclass_map: ClassVar[MutableMapping[Scheme, type]] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__()
        for scheme in cls._allowed_schemes():
            if scheme in Url.subclass_map:
                raise ValueError(f'"{scheme}" is already reserved by '
                                 f'"{cls.subclass_map[scheme].__qualname__}"')
            Url.subclass_map[scheme] = cls

    @abstractmethod
    def __init__(self, url: str):
        pass

    @abstractmethod
    def request(self) -> Response:
        pass

    @classmethod
    @abstractmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        pass

    @staticmethod
    def create_from(url: str):
        scheme, _ = url.split(':', 1)
        try:
            klass = Url.subclass_map[Scheme(scheme)]
        except ValueError:
            raise InvalidSchemeError(scheme)
        return klass(url)
