# pybcl

<p align="left">
<a><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/pybcl"></a>
<a href="https://pypi.org/project/pybcl/"><img alt="PyPI" src="https://img.shields.io/pypi/v/pybcl"></a>
<a href="https://github.com/AT0myks/pybcl/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/pybcl"></a>
</p>

* [Algorithms](#algorithms)
* [Requirements](#requirements)
* [Installation](#installation)
* [Usage](#usage)
* [Header variant](#header-variant)
* [Original library](#original-library)

This project brings the basic compression library (BCL) to Python.
These are not bindings, the wrapped library is bundled in the compiled binary.
A [few changes](https://github.com/AT0myks/pybcl/commit/5555256e39648f040f41f3ee4da2b8d4316e8ec1)
have been made to the original BCL in order to (hopefully) prevent segmentation
faults for LZ77 and RLE decompression, and to ease the development of the module.

## Algorithms

The BCL contains a C implementation of these five algorithms:
- Huffman
- Lempel-Ziv (LZ77)
- Rice
- RLE (Run-length encoding)
- Shannon-Fano

## Requirements

Python 3.7+

## Installation

```
pip install pybcl
```

## Usage

> [!CAUTION]
> While there's been an effort to prevent buffer overflows for the RLE and LZ77
> decompression algorithms, the other three are very likely to segfault if you
> give them corrupt/random data.

### API

```py
from pybcl import compress, decompress, ...

# Functions exposed by the C extension.
def compress(data, algo, header=False): ...
def decompress(data, algo=0, outsize=0): ...

# Shortcut functions.
def huffman_compress(data, header=False): ...
def lz_compress_fast(data, header=False): ...
def rice_compress(data, format, header=False): ...
def rle_compress(data, header=False): ...
def sf_compress(data, header=False): ...

def huffman_decompress(data, outsize=0): ...
def lz_decompress(data, outsize=0): ...
def rice_decompress(data, format, outsize=0): ...
def rle_decompress(data, outsize=0): ...
def sf_decompress(data, outsize=0): ...
```

For compression you can choose whether the header should be included in the result.

For decompression you can override `outsize` by giving a positive value. `algo`
and `outsize` aren't required if the data contains a header.

Two enums are provided for the algorithms and Rice formats. Example:

```py
from pybcl import Algorithm, RiceFormat

data = b"test"
compressed = compress(data, Algorithm.RICE8)
decompressed = rice_decompress(compressed, RiceFormat.UINT8, len(data))
```

### Command line

Compression:

```
usage: pybcl c [-h] [-a ALGO] [-o OFFSET] [-m SIZE] [-f] [--no-header] src dest

positional arguments:
  src                         input file
  dest                        output file

options:
  -h, --help                  show this help message and exit
  -a ALGO, --algo ALGO        algorithm for (de)compression. Not required for decompression if a header is present
  -o OFFSET, --offset OFFSET  position in src where to start reading from
  -m SIZE, --maxread SIZE     max amount of bytes to read from src. Default: all that can be read
  -f, --force                 overwrite dest
  --no-header                 do not write a header for the file
```

Decompression:

```
usage: pybcl d [-h] [-a ALGO] [-o OFFSET] [-m SIZE] [-f] [-s SIZE] [--hvariant] src dest

positional arguments:
  src                         input file
  dest                        output file

options:
  -h, --help                  show this help message and exit
  -a ALGO, --algo ALGO        algorithm for (de)compression. Not required for decompression if a header is present
  -o OFFSET, --offset OFFSET  position in src where to start reading from
  -m SIZE, --maxread SIZE     max amount of bytes to read from src. Default: all that can be read
  -f, --force                 overwrite dest
  -s SIZE, --outsize SIZE     required if no header
  --hvariant                  force reading the header variant
```

When decompressing data that has a header with LZ77 or RLE, if you get an
`OutputOverrun` error you can override the header's outsize to specify a higher value.

## Header variant

Some camera firmwares contain parts that are compressed with a modified version
of the BCL that adds the size of the compressed data to the header and replaces
two of the always empty bytes of the algo by unknown data (maybe a checksum).
A `HeaderVariant` class is provided for this specific case. For now only the CLI
makes use of this class. Note that this has nothing to do with the original
library and is only included because I need it for another project.
See [here](https://reverseengineering.stackexchange.com/questions/6591/non-standard-lz77-compression-header)
for an example.

## Original library

The BCL is written by [Marcus Geelnard](https://github.com/mbitsnbites) and
licensed under the terms of the zlib license.

You can find it here:

- https://web.archive.org/web/20181025055443/http://bcl.comli.eu/
- https://sourceforge.net/projects/bcl/
- https://github.com/mbitsnbites/bcl
- https://gitlab.com/mbitsnbites/bcl

It comes with the basic file compressor, or BFC, which is a test application for
the BCL. Data compressed with the BFC starts with the `BCL1` magic.