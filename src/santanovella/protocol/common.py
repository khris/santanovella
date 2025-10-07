from abc import ABCMeta, abstractmethod
from enum import StrEnum, auto
from typing import ClassVar, MutableMapping, Iterable


class Scheme(StrEnum):
    HTTP = auto()
    HTTPS = auto()
    FILE = auto()


class Url(metaclass=ABCMeta):
    subclass_map: ClassVar[MutableMapping[Scheme, type]] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__()
        for scheme in cls._allowed_schemes():
            if scheme in Url.subclass_map:
                raise ValueError(f'"{scheme}" is already reserved by "{cls.subclass_map[scheme].__qualname__}"')
            Url.subclass_map[scheme] = cls

    @abstractmethod
    def __init__(self, url: str):
        pass

    @abstractmethod
    def request(self):
        pass

    @classmethod
    @abstractmethod
    def _allowed_schemes(cls) -> Iterable[Scheme]:
        pass

    @staticmethod
    def create_from(url: str):
        scheme, _ = url.split(':', 1)
        klass = Url.subclass_map[Scheme(scheme)]
        return klass(url)
