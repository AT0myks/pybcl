from __future__ import annotations

import sys
from ctypes import BigEndianStructure, c_char, c_ubyte, c_uint32, sizeof
from enum import IntEnum
from typing import BinaryIO, Union

if sys.version_info >= (3, 9):
    from collections.abc import Iterable
else:
    from typing import Iterable

if sys.version_info >= (3, 11):
    from typing import Self
    SelfHeader = Self
else:
    from typing import TypeVar
    SelfHeader = TypeVar("SelfHeader", bound="_Header")

if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from typing import ByteString as Buffer

from pybcl._bcl import *
from pybcl._bcl import (
    BCL_ALGO_HUFFMAN,
    BCL_ALGO_LZ77,
    BCL_ALGO_RICE8,
    BCL_ALGO_RICE16,
    BCL_ALGO_RICE32,
    BCL_ALGO_RICE8S,
    BCL_ALGO_RICE16S,
    BCL_ALGO_RICE32S,
    BCL_ALGO_RLE,
    BCL_ALGO_SF,

    BCL_MAGIC,

    RICE_FMT_INT8,
    RICE_FMT_UINT8,
    RICE_FMT_INT16,
    RICE_FMT_UINT16,
    RICE_FMT_INT32,
    RICE_FMT_UINT32,

    compress,
    decompress,
)

__version__ = "1.0.0"

BCL_MAGIC_BYTES: bytes = BCL_MAGIC.encode()

RICEFMT_TO_ALGO = {
    RICE_FMT_INT8: BCL_ALGO_RICE8S,
    RICE_FMT_UINT8: BCL_ALGO_RICE8,
    RICE_FMT_INT16: BCL_ALGO_RICE16S,
    RICE_FMT_UINT16: BCL_ALGO_RICE16,
    RICE_FMT_INT32: BCL_ALGO_RICE32S,
    RICE_FMT_UINT32: BCL_ALGO_RICE32,
}


class Algorithm(IntEnum):
    HUFFMAN = BCL_ALGO_HUFFMAN
    LZ77 = BCL_ALGO_LZ77
    RICE8 = BCL_ALGO_RICE8
    RICE16 = BCL_ALGO_RICE16
    RICE32 = BCL_ALGO_RICE32
    RICE8S = BCL_ALGO_RICE8S
    RICE16S = BCL_ALGO_RICE16S
    RICE32S = BCL_ALGO_RICE32S
    RLE = BCL_ALGO_RLE
    SF = BCL_ALGO_SF


class RiceFormat(IntEnum):
    INT8 = RICE_FMT_INT8
    UINT8 = RICE_FMT_UINT8
    INT16 = RICE_FMT_INT16
    UINT16 = RICE_FMT_UINT16
    INT32 = RICE_FMT_INT32
    UINT32 = RICE_FMT_UINT32


class _Header(BigEndianStructure):

    _magic: bytes
    _empty0: bytes
    _algo: int
    _outsize: int

    def __iter__(self) -> Iterable[tuple[str, Union[bytes, int, str]]]:
        for name, _ in self._fields_:
            prop = name.lstrip('_')
            try:
                yield prop, getattr(self, prop)
            except AttributeError:
                yield name, getattr(self, name)

    @property
    def magic(self) -> str:
        return self._magic.decode()

    @property
    def algo(self) -> int:
        """The algorithm used for compression."""
        return self._algo

    @property
    def outsize(self) -> int:
        """The size of the original uncompressed data."""
        return self._outsize

    @classmethod
    def from_fd(cls, fd: BinaryIO) -> SelfHeader:
        return cls.from_buffer_copy(fd.read(sizeof(cls)))


class Header(_Header):
    _fields_ = [
        ("_magic", c_char * 4),
        ("_empty0", c_char * 3),
        ("_algo", c_ubyte),
        ("_outsize", c_uint32),
    ]


class HeaderVariant(_Header):
    """A variant that appears in some camera firmwares."""
    _fields_ = [
        ("_magic", c_char * 4),
        ("_empty0", c_char * 3),  # 2 first bytes are not empty
        ("_algo", c_ubyte),
        ("_outsize", c_uint32),
        ("_size", c_uint32),
    ]
    _size: int

    @property
    def size(self) -> int:
        """The size of the compressed data."""
        return self._size


# Compress


def huffman_compress(data: Buffer, header: bool = False) -> bytes:
    return compress(data, BCL_ALGO_HUFFMAN, header)


def lz_compress_fast(data: Buffer, header: bool = False) -> bytes:
    return compress(data, BCL_ALGO_LZ77, header)


def rice_compress(data: Buffer, format: int, header: bool = False) -> bytes:
    if not isinstance(format, int):
        raise TypeError("format must be an int")
    try:
        algo = RICEFMT_TO_ALGO[format]
    except KeyError:
        raise ValueError(f"Unknown Rice format {format}") from None
    return compress(data, algo, header)


def rle_compress(data: Buffer, header: bool = False) -> bytes:
    return compress(data, BCL_ALGO_RLE, header)


def sf_compress(data: Buffer, header: bool = False) -> bytes:
    return compress(data, BCL_ALGO_SF, header)


# Decompress


def huffman_decompress(data: Buffer, outsize: int = 0) -> bytes:
    return decompress(data, BCL_ALGO_HUFFMAN, outsize)


def lz_decompress(data: Buffer, outsize: int = 0) -> bytes:
    return decompress(data, BCL_ALGO_LZ77, outsize)


def rice_decompress(data: Buffer, format: int, outsize: int = 0) -> bytes:
    if not isinstance(format, int):
        raise TypeError("format must be an int")
    try:
        algo = RICEFMT_TO_ALGO[format]
    except KeyError:
        raise ValueError(f"Unknown Rice format {format}") from None
    return decompress(data, algo, outsize)


def rle_decompress(data: Buffer, outsize: int = 0) -> bytes:
    return decompress(data, BCL_ALGO_RLE, outsize)


def sf_decompress(data: Buffer, outsize: int = 0) -> bytes:
    return decompress(data, BCL_ALGO_SF, outsize)
