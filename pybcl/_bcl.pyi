import sys
if sys.version_info >= (3, 12):
    from collections.abc import Buffer
else:
    from typing import ByteString as Buffer


BCL_HEADER_SIZE: int
BCL_MAGIC: str

RICE_FMT_INT8: int
RICE_FMT_UINT8: int
RICE_FMT_INT16: int
RICE_FMT_UINT16: int
RICE_FMT_INT32: int
RICE_FMT_UINT32: int

BCL_ALGO_HUFFMAN: int
BCL_ALGO_LZ77: int
BCL_ALGO_RICE8: int
BCL_ALGO_RICE16: int
BCL_ALGO_RICE32: int
BCL_ALGO_RICE8S: int
BCL_ALGO_RICE16S: int
BCL_ALGO_RICE32S: int
BCL_ALGO_RLE: int
BCL_ALGO_SF: int


class BCLError(Exception): ...


class InputOverrun(BCLError): ...


class OutputOverrun(BCLError): ...


def compress(data: Buffer, algo: int, header: bool = False) -> bytes: ...


def decompress(data: Buffer, algo: int = 0, outsize: int = 0) -> bytes: ...
