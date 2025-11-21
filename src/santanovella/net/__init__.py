import functools
import logging
import ssl
import weakref
from abc import abstractmethod, ABC
from collections import namedtuple
from collections.abc import Callable
from socket import socket, AF_INET, IPPROTO_TCP, MSG_PEEK, MSG_DONTWAIT, \
    SOCK_STREAM
from typing import BinaryIO

MAX_RETRIES = 3
ConnectionKey = namedtuple('ConnectionKey', 'host, port, is_secure')


def _retryable(*, max_retries: int = MAX_RETRIES) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: '_Connection', *args, **kwargs):
            retry_count = 0
            while True:
                try:
                    return func(self, *args, **kwargs)
                except ConnectionResetError as e:
                    if retry_count >= max_retries:
                        raise e
                    else:
                        self.close()
                        self.connect()

        return wrapper

    return decorator


class Connection(ABC):
    @property
    @abstractmethod
    def alive(self) -> bool:
        pass

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def send(self, data: bytes) -> int:
        pass

    @abstractmethod
    def recv(self) -> BinaryIO:
        pass

    @abstractmethod
    def close(self, *, safety=False) -> None:
        pass


class _Connection(Connection):
    _host: str
    _port: int
    _is_secure: bool
    _closed: bool = False
    _sock: socket

    def __init__(self, host: str, port: int, is_secure: bool) -> None:
        self._host = host
        self._port = port
        self._is_secure = is_secure
        self._closed = False
        s = socket(
            family=AF_INET,
            type=SOCK_STREAM,
            proto=IPPROTO_TCP,
        )

        if is_secure:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=host)

        s.connect((host, port))
        self._sock = s

        weakref.finalize(self, self._at_finalized)

    def __repr__(self):
        return f'_Connection([{"secure" if self._is_secure else "non-secure"}] {self._host}:{self._port})'

    def _at_finalized(self):
        logging.debug('%s is finalized, socket closing', repr(self))
        self.close()

    @property
    def alive(self) -> bool:
        try:
            if self._closed:
                return False
            data = self._sock.recv(1, MSG_PEEK | MSG_DONTWAIT)
            return bool(data)
        except BlockingIOError:
            return True
        except ConnectionResetError:
            return False

    def connect(self) -> None:
        s = socket(
            family=AF_INET,
            type=SOCK_STREAM,
            proto=IPPROTO_TCP,
        )

        if self._is_secure:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self._host)

        s.connect((self._host, self._port))
        self._sock = s
        self._closed = False
        logging.debug('%s is connected', repr(self))

    @_retryable(max_retries=MAX_RETRIES)
    def send(self, data: bytes) -> int:
        sent_bytes = self._sock.send(data)
        logging.debug('%s sent %d byte(s)', repr(self), sent_bytes)
        return sent_bytes

    @_retryable(max_retries=MAX_RETRIES)
    def recv(self) -> BinaryIO:
        io_object = self._sock.makefile(mode='rb', newline='\r\n')
        logging.debug('%s maked file for receiving', repr(self))
        return io_object

    def close(self, *, safety=True) -> None:
        try:
            self._closed = True
            logging.debug('%s closed', repr(self))
            self._sock.close()
        except Exception as e:
            if not safety:
                raise e


class SocketPool:
    _conns: dict[ConnectionKey, Connection]
    _initialized: bool = False

    @functools.cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self):
        self._initialize()

    def _initialize(self):
        if not self._initialized:
            self._conns = {}
            self._initialized = True

    def get_connection(
            self, host: str, port: int, is_secure: bool) -> Connection:
        key = ConnectionKey(host, port, is_secure)
        if key not in self._conns:
            self._conns[key] = _Connection(host, port, is_secure)
        else:
            conn = self._conns[key]
            if not conn.alive:
                conn.close()
                conn.connect()

        return self._conns[key]
