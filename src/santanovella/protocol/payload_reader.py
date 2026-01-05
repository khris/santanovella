import logging
from abc import ABC, abstractmethod
from compression import gzip, zlib
from enum import Enum, auto
from typing import BinaryIO


class PayloadReader(ABC):
    @abstractmethod
    def read(self, src: BinaryIO, *, length=-1) -> bytes:
        pass

    @classmethod
    def create_for(cls, content_encoding: str) -> 'PayloadReader':
        match content_encoding:
            case 'chunked':
                return ChunkReader()
            case 'deflate':
                return DeflateReader()
            case 'gzip':
                return GzipReader()
            case 'identity':
                return PlainTextReader()
            case _:
                logging.warning(f'Unsupported encoding: {content_encoding}')
                return PlainTextReader()


class PlainTextReader(PayloadReader):
    def read(self, src: BinaryIO, *, length=-1) -> bytes:
        return src.read(length)


class GzipReader(PayloadReader):
    def read(self, src: BinaryIO, *, length=-1) -> bytes:
        payload = src.read(length)
        return gzip.decompress(payload)


class DeflateReader(PayloadReader):
    def read(self, src: BinaryIO, *, length=-1) -> bytes:
        payload = src.read(length)
        return zlib.decompress(payload)


class ChunkReader(PayloadReader):
    class Mode(Enum):
        Length = auto()
        Chunk = auto()

    def read(self, src: BinaryIO, *, length=-1) -> bytes:
        mode = self.Mode.Length
        length = 0
        content = bytearray()
        buf = bytearray()
        while True:
            match mode:
                case self.Mode.Length:
                    if (first := src.read(1)) == b'\r':
                        if (second := src.read(1)) == b'\n':
                            length = int(buf, base=16)
                            if length == 0:
                                return bytes(content)
                            else:
                                print(f"Reading chunk of size {length}")
                                buf.clear()
                                mode = self.Mode.Chunk
                        else:
                            buf += first
                            buf += second
                    else:
                        buf += first

                case self.Mode.Chunk:
                    buf += src.read(1)

                    if len(buf) < length:
                        continue

                    if (delimiter := src.read(2)) != b'\r\n':
                        raise Exception(f"Invalid chunk delimiter: {delimiter}")

                    print(f"Chunk(len={len(buf)}) read: {buf!r}")
                    content += buf
                    buf.clear()
                    mode = self.Mode.Length
