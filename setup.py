import os
import posixpath

from setuptools import Extension, setup

bcl_dir = os.environ.get("BCL_DIR", "bcl")  # Relative path.
bcl_src = posixpath.join(bcl_dir, "src")

sources = [
    posixpath.join(bcl_src, "huffman.c"),
    posixpath.join(bcl_src, "lz.c"),
    posixpath.join(bcl_src, "rice.c"),
    posixpath.join(bcl_src, "rle.c"),
    posixpath.join(bcl_src, "shannonfano.c"),
    "bclmodule.c"
]

setup(
    ext_modules=[
        Extension(
            name="pybcl._bcl",
            sources=sources,
            include_dirs=[bcl_src],
        )
    ],
)
