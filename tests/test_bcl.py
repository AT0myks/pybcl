import sys
from ctypes import c_uint
from pathlib import Path

import pytest

import pybcl

emptybytes = b''
testdir = Path(__file__).parent
loremipsum = (testdir / "loremipsum.txt").read_bytes()
overflow_value = c_uint(-1).value + 1
algos = [
    pybcl.Algorithm.HUFFMAN,
    pybcl.Algorithm.LZ77,
    pybcl.Algorithm.RICE8,
    pybcl.Algorithm.RICE8S,
    pybcl.Algorithm.RICE16,
    pybcl.Algorithm.RICE16S,
    pybcl.Algorithm.RICE32,
    pybcl.Algorithm.RICE32S,
    pybcl.Algorithm.RLE,
    pybcl.Algorithm.SF,
]
algo_to_ricefmt = {
    pybcl.BCL_ALGO_RICE8S: pybcl.RICE_FMT_INT8,
    pybcl.BCL_ALGO_RICE8: pybcl.RICE_FMT_UINT8,
    pybcl.BCL_ALGO_RICE16S: pybcl.RICE_FMT_INT16,
    pybcl.BCL_ALGO_RICE16: pybcl.RICE_FMT_UINT16,
    pybcl.BCL_ALGO_RICE32S: pybcl.RICE_FMT_INT32,
    pybcl.BCL_ALGO_RICE32: pybcl.RICE_FMT_UINT32,
}


@pytest.mark.parametrize(
    "algo",
    [
        pybcl.Algorithm.HUFFMAN,
        pybcl.Algorithm.LZ77,
        pybcl.Algorithm.RICE8,
        pybcl.Algorithm.RICE8S,
        pytest.param(pybcl.Algorithm.RICE16, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE16S, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32S, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pybcl.Algorithm.RLE,
        pybcl.Algorithm.SF,
    ]
)
def test_roundtrip_with_header(algo):
    comp = pybcl.compress(loremipsum, algo, True)
    assert pybcl.decompress(comp) == loremipsum, algo
    assert pybcl.decompress(comp, algo, len(loremipsum)) == loremipsum, algo


@pytest.mark.parametrize(
    "algo",
    [
        pybcl.Algorithm.HUFFMAN,
        pybcl.Algorithm.LZ77,
        pybcl.Algorithm.RICE8,
        pybcl.Algorithm.RICE8S,
        pytest.param(pybcl.Algorithm.RICE16, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE16S, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32S, marks=pytest.mark.xfail(reason="same as bfc", strict=True)),
        pybcl.Algorithm.RLE,
        pybcl.Algorithm.SF,
    ]
)
def test_roundtrip_without_header(algo):
    comp = pybcl.compress(loremipsum, algo, False)
    assert pybcl.decompress(comp, algo, len(loremipsum)) == loremipsum, algo


@pytest.mark.parametrize(
    "algo",
    [
        pybcl.Algorithm.HUFFMAN,
        pybcl.Algorithm.LZ77,
        pybcl.Algorithm.RICE8,
        pybcl.Algorithm.RICE8S,
        pytest.param(pybcl.Algorithm.RICE16, marks=pytest.mark.xfail(sys.byteorder=="big", reason="big-endian", strict=True)),
        pytest.param(pybcl.Algorithm.RICE16S, marks=pytest.mark.xfail(sys.byteorder=="big", reason="big-endian", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32, marks=pytest.mark.xfail(sys.byteorder=="big", reason="big-endian", strict=True)),
        pytest.param(pybcl.Algorithm.RICE32S, marks=pytest.mark.xfail(sys.byteorder=="big", reason="big-endian", strict=True)),
        pybcl.Algorithm.RLE,
        pybcl.Algorithm.SF,
    ]
)
def test_compare_to_bfc(algo):
    control = (testdir / f"bfc_comp_{algo.name.lower()}").read_bytes()
    assert pybcl.compress(loremipsum, algo, True) == control


@pytest.mark.parametrize("algo", algos)
@pytest.mark.parametrize("data", [loremipsum, emptybytes])
def test_header_algo(algo, data):
    comp = pybcl.compress(data, algo, True)
    hdr = pybcl.Header.from_buffer_copy(comp)
    assert hdr._algo == algo


@pytest.mark.parametrize("algo", algos)
@pytest.mark.parametrize("data", [loremipsum, emptybytes])
def test_header_outsize(algo, data):
    comp = pybcl.compress(data, algo, True)
    hdr = pybcl.Header.from_buffer_copy(comp)
    assert hdr._outsize == len(data)


@pytest.mark.parametrize("algo", algos)
def test_header_size(algo):
    hdr = pybcl.compress(loremipsum, algo, True)
    nohdr = pybcl.compress(loremipsum, algo, False)
    assert len(hdr) - len(nohdr) == pybcl.BCL_HEADER_SIZE


@pytest.mark.parametrize("algo", algos)
def test_with_and_without_header(algo):
    hdr = pybcl.compress(loremipsum, algo, True)
    nohdr = pybcl.compress(loremipsum, algo, False)
    assert hdr[pybcl.BCL_HEADER_SIZE:] == nohdr


@pytest.mark.parametrize(
    ("const", "expected"),
    [
        (pybcl.BCL_HEADER_SIZE, 12),
        (pybcl.BCL_MAGIC, "BCL1"),
        (pybcl.BCL_MAGIC_BYTES, b"BCL1"),

        (pybcl.BCL_ALGO_RLE, 1),
        (pybcl.BCL_ALGO_HUFFMAN, 2),
        (pybcl.BCL_ALGO_RICE8, 3),
        (pybcl.BCL_ALGO_RICE16, 4),
        (pybcl.BCL_ALGO_RICE32, 5),
        (pybcl.BCL_ALGO_RICE8S, 6),
        (pybcl.BCL_ALGO_RICE16S, 7),
        (pybcl.BCL_ALGO_RICE32S, 8),
        (pybcl.BCL_ALGO_LZ77, 9),
        (pybcl.BCL_ALGO_SF, 10),

        (pybcl.RICE_FMT_INT8, 1),
        (pybcl.RICE_FMT_UINT8, 2),
        (pybcl.RICE_FMT_INT16, 3),
        (pybcl.RICE_FMT_UINT16, 4),
        (pybcl.RICE_FMT_INT32, 7),
        (pybcl.RICE_FMT_UINT32, 8),
    ]
)
def test_constants(const, expected):
    assert const == expected


@pytest.mark.parametrize("algo", [pybcl.Algorithm.LZ77, pybcl.Algorithm.RLE])
def test_input_overrun(algo):
    with pytest.raises(pybcl.InputOverrun):
        pybcl.decompress(bytearray(500), algo, outsize=5000)


@pytest.mark.parametrize("algo", [pybcl.Algorithm.LZ77, pybcl.Algorithm.RLE])
def test_output_overrun(algo):
    # sf and huffman cannot output overrun
    comp = pybcl.compress(loremipsum, algo, True)
    with pytest.raises(pybcl.OutputOverrun):
        pybcl.decompress(comp, outsize=5)


@pytest.mark.parametrize("algo", [pybcl.Algorithm.LZ77, pybcl.Algorithm.RLE])
def test_correct_outsize(algo):
    comp = pybcl.compress(loremipsum, algo, True)
    larger_outsize = len(loremipsum) + 1
    assert len(pybcl.decompress(comp, outsize=larger_outsize)) == len(loremipsum)


@pytest.mark.parametrize("algo", algos)
@pytest.mark.parametrize("func", [pybcl.compress, pybcl.decompress])
def test_unknown_algo_arg(algo, func):
    with pytest.raises(pybcl.BCLError, match="Unknown algo .*"):
        func(b'0', 0, 1)


@pytest.mark.parametrize("algo", algos)
def test_unknown_algo_header(algo):
    data = pybcl.BCL_MAGIC_BYTES + bytes(9)
    with pytest.raises(pybcl.BCLError, match="Unknown algo .*"):
        pybcl.decompress(data, outsize=1)


@pytest.mark.parametrize(
    ("func", "algo"),
    [
        (pybcl.huffman_decompress, pybcl.BCL_ALGO_HUFFMAN),
        (pybcl.lz_decompress, pybcl.BCL_ALGO_LZ77),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE8),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE8S),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE16),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE16S),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE32),
        (pybcl.rice_decompress, pybcl.BCL_ALGO_RICE32S),
        (pybcl.rle_decompress, pybcl.BCL_ALGO_RLE),
        (pybcl.sf_decompress, pybcl.BCL_ALGO_SF),
    ]
)
def test_algo_header_doesnt_match(func, algo):
    data = pybcl.BCL_MAGIC_BYTES + bytes(8)
    with pytest.raises(pybcl.BCLError, match=f"Header's algo 0 is different from the requested one {algo}"):
        if func == pybcl.rice_decompress:
            func(data, algo_to_ricefmt[algo], outsize=1)
        else:
            func(data, outsize=1)


@pytest.mark.skipif(sys.maxsize < overflow_value, reason="32-bit")
def test_overflow():
    with pytest.raises(OverflowError, match=f"Output buffer size does not fit in an unsigned int: {overflow_value}"):
        pybcl.decompress(b'0', outsize=overflow_value)


@pytest.mark.parametrize("algo", algos)
@pytest.mark.parametrize("cls", [bytes, memoryview, bytearray])
def test_arg_type(algo, cls):
    arg = cls(loremipsum)
    comp = pybcl.compress(arg, algo, header=True)
    pybcl.decompress(cls(comp))


@pytest.mark.parametrize("algo", algos)
def test_kwargs(algo):
    comp = pybcl.compress(loremipsum, algo, header=True)
    pybcl.decompress(comp, algo=algo, outsize=len(loremipsum))


@pytest.mark.parametrize("algo", algos)
def test_comp_empty(algo):
    assert pybcl.compress(emptybytes, algo) == emptybytes


@pytest.mark.parametrize("algo", algos)
def test_decomp_empty(algo):
    assert pybcl.decompress(emptybytes, algo, 1) == emptybytes


@pytest.mark.parametrize("algo", algos)
def test_roundtrip_empty(algo):
    comp = pybcl.compress(emptybytes, algo, True)
    assert pybcl.decompress(comp) == emptybytes


def test_header_outsize_override():
    algo = pybcl.BCL_ALGO_LZ77
    comp = pybcl.compress(loremipsum, algo, header=True)
    with pytest.raises(pybcl.OutputOverrun, match="Output overrun or output buffer too small: .*"):
        pybcl.decompress(comp, algo=algo, outsize=len(loremipsum)-1)


@pytest.mark.parametrize("algo", algos)
def test_headerless_requires_outsize(algo):
    comp = pybcl.compress(loremipsum, algo, header=False)
    with pytest.raises(pybcl.BCLError, match="Valid outsize required if no header"):
        pybcl.decompress(comp, algo)


@pytest.mark.parametrize("algo", algos)
def test_invalid_outsize_with_header(algo):
    # When there is a header, its outsize is used
    # in case the given one is invalid.
    comp = pybcl.compress(loremipsum, algo, header=True)
    pybcl.decompress(comp, algo, -1)


@pytest.mark.parametrize("algo", algos)
def test_invalid_outsize_without_header(algo):
    comp = pybcl.compress(loremipsum, algo, header=False)
    with pytest.raises(pybcl.BCLError, match="Valid outsize required if no header"):
        pybcl.decompress(comp, algo, -1)


@pytest.mark.parametrize("algo", [pybcl.BCL_ALGO_HUFFMAN, pybcl.BCL_ALGO_SF])
def test_sf_huff_outsize(algo):
    size = 5
    comp = pybcl.compress(loremipsum, algo)
    decomp = pybcl.decompress(comp, algo, size)
    assert size == len(decomp)
