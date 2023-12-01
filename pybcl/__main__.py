import argparse
import sys
from ctypes import sizeof
from pathlib import Path

from pybcl import (
    BCL_HEADER_SIZE,
    BCL_MAGIC_BYTES,
    Algorithm,
    Header,
    HeaderVariant,
    compress,
    decompress,
    __version__
)

DEFAULT_ALGO = 0
DEFAULT_MAXREAD = -1
DEFAULT_OFFSET = 0
DEFAULT_OUTSIZE = 0


def comp(
    src: Path,
    dest: Path,
    algo: int,
    offset: int = DEFAULT_OFFSET,
    maxread: int = DEFAULT_MAXREAD,
    header: bool = True
) -> int:
    with open(src, "rb") as f:
        f.seek(offset)
        data = f.read(maxread)
    if maxread != DEFAULT_MAXREAD and len(data) != maxread:
        raise Exception("read returned less bytes than expected")
    compressed = compress(data, algo, header)
    return dest.write_bytes(compressed)


def _comp(args: argparse.Namespace, algo: int) -> None:
    if not isinstance(algo, Algorithm):
        raise Exception("No algorithm specified")
    print(f"Compressing {args.src} to {args.dest} using {algo.name}")
    size = comp(args.src, args.dest, algo, args.offset, args.maxread, not args.no_header)
    print(f"Compression done, wrote {size:,} bytes.")


def decomp(
    src: Path,
    dest: Path,
    algo: int = DEFAULT_ALGO,
    offset: int = DEFAULT_OFFSET,
    maxread: int = DEFAULT_MAXREAD,
    outsize: int = DEFAULT_OUTSIZE,
    hvariant: bool = False
) -> int:
    src_size = src.stat().st_size
    if maxread < 1:
        maxread = src_size - offset
    with open(src, "rb") as f:
        f.seek(offset)
        if hvariant:
            hdr = HeaderVariant.from_fd(f)
            if hdr._magic != BCL_MAGIC_BYTES:
                raise Exception(f"BCL magic not found at offset {offset}")
            comp_size = hdr.size
        else:
            hdr = None
            comp_size = src_size - offset
            if comp_size > BCL_HEADER_SIZE:  # There might be a header.
                hdr = HeaderVariant.from_fd(f)
                if hdr._magic != BCL_MAGIC_BYTES:
                    hdr = None  # Assume there's no header.
                    f.seek(-sizeof(HeaderVariant), 1)
                elif hdr.size != comp_size - sizeof(HeaderVariant):
                    f.seek(-sizeof(HeaderVariant), 1)
                    hdr = Header.from_fd(f)  # Assume it's an original header.
                    comp_size -= sizeof(Header)
                else:
                    comp_size = hdr.size
        comp_size = min(comp_size, maxread)
        compressed = f.read(comp_size)
    if len(compressed) != comp_size:
        raise Exception("read returned less bytes than expected")
    if hdr is not None:
        algo = algo or hdr.algo
        outsize = outsize or hdr.outsize
    if algo == DEFAULT_ALGO:
        raise Exception("Must specify algo if no header")
    if outsize == DEFAULT_OUTSIZE or outsize < 1:
        raise Exception("Must specify valid outsize if no header")
    decompressed = decompress(compressed, algo, outsize)
    return dest.write_bytes(decompressed)


def _decomp(args: argparse.Namespace, algo: int) -> None:
    print(f"Decompressing {args.src} to {args.dest}")
    size = decomp(args.src, args.dest, algo, args.offset, args.maxread, args.outsize, args.hvariant)
    print(f"Decompression done, wrote {size:,} bytes.")


def main():
    algos = [name.lower() for name in Algorithm._member_names_]

    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(required=True, dest="command")  # dest is only here to avoid a TypeError in Python 3.7 and 3.8 (see bpo-29298)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("src", type=Path, help="input file")
    common.add_argument("dest", type=Path, help="output file")
    common.add_argument("-a", "--algo", choices=algos, default=DEFAULT_ALGO, metavar="ALGO", help="algorithm for (de)compression. Not required for decompression if a header is present")
    common.add_argument("-o", "--offset", type=int, default=DEFAULT_OFFSET, help="position in src where to start reading from")
    common.add_argument("-m", "--maxread", type=int, default=DEFAULT_MAXREAD, metavar="SIZE", help="max amount of bytes to read from src. Default: all that can be read")
    common.add_argument("-f", "--force", action="store_true", help="overwrite dest")

    parser_c = subparsers.add_parser('c', parents=[common], help="compress")
    parser_c.add_argument("--no-header", action="store_true", help="do not write a header for the file")
    parser_c.set_defaults(func=_comp)

    parser_d = subparsers.add_parser('d', parents=[common], help="decompress")
    parser_d.add_argument("-s", "--outsize", type=int, default=DEFAULT_OUTSIZE, metavar="SIZE", help="required if no header")
    parser_d.add_argument("--hvariant", action="store_true", help="force reading the header variant")
    parser_d.set_defaults(func=_decomp)

    args = parser.parse_args()
    if not args.src.exists():
        sys.exit("error: src does not exist")
    if args.dest.exists() and not args.force:
        sys.exit("error: dest already exists")
    if args.offset is not None:
        if args.offset >= args.src.stat().st_size:
            sys.exit("error: offset larger than file size")
        elif args.offset < 0:
            sys.exit("error: offset cannot be negative")
    algo = Algorithm[args.algo.upper()] if args.algo != DEFAULT_ALGO else 0
    try:
        args.func(args, algo)
    except Exception as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
