from collections import namedtuple
from collections.abc import Sequence
from time import monotonic_ns
from typing import Generic, NamedTuple, TypeVar

K = TypeVar('K')
V = TypeVar('V')


class SimpleKV(NamedTuple, Generic[K, V]):
    key: K
    value: V

    @classmethod
    def from_seq(cls, seq: Sequence[K], /):
        match seq:
            case [key]:
                return cls(key=key, value=None)
            case [key, value]:
                return cls(key=key, value=value)
            case _:
                raise TypeError(f'input expected at most 1 or 2 argument(s), '
                                f'got {len(seq)}')



_Value = namedtuple('_Value', 'value, expire_at')


class TtlCache(Generic[K, V]):

    def __init__(self):
        self._cache = dict[K, _Value]()

    def __delitem__(self, key, /):
        self._cache.pop(key, None)

    def __getitem__(self, key, /):
        value = self._cache.get(key, None)
        if not value or value.expire_at <= _now():
            raise KeyError(key)
        return value.value

    def __len__(self):
        self._purge_expired()
        return len(self._cache)

    def set(self, key: K, value: V, *, ttl_in_ms: int):
        self._cache[key] = _Value(value, _now() + ttl_in_ms)

    def get(self, key: K, default: V | None = None, /):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def _purge_expired(self):
        now = _now()
        self._cache = {k: v for k, v in self._cache.items() if v.expire_at <= now}


def _now():
    return monotonic_ns() // 1e+6
