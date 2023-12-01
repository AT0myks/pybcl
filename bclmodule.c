#define PY_SSIZE_T_CLEAN
#include <Python.h>

#if SIZE_MAX < UINT_MAX
#  error "SIZE_MAX must be >= UINT_MAX"
#endif

#include "bcl.h"
#include "huffman.h"
#include "lz.h"
#include "rice.h"
#include "rle.h"
#include "shannonfano.h"

#ifndef _PyCFunction_CAST
#  define _PyCFunction_CAST(func) ((PyCFunction)(void(*)(void))(func))
#endif

static PyObject *BCLError;
static PyObject *InputOverrun;
static PyObject *OutputOverrun;

int
read_header(unsigned char *in, unsigned char *algo, unsigned int *size)
{
    if (memcmp(in, BCL_MAGIC, 4) != 0) {
        return -1;
    }
    *algo = (((unsigned int)in[4])<<24) +
            (((unsigned int)in[5])<<16) +
            (((unsigned int)in[6])<<8)  +
              (unsigned int)in[7];
    *size = (((unsigned int)in[8])<<24) +
            (((unsigned int)in[9])<<16) +
            (((unsigned int)in[10])<<8) +
              (unsigned int)in[11];
    return 0;
}

void
write_header(unsigned char *out, unsigned char algo, unsigned int size)
{
    memcpy(out, BCL_MAGIC, 4);
    out[4]  = (algo>>24) & 255;
    out[5]  = (algo>>16) & 255;
    out[6]  = (algo>>8)  & 255;
    out[7]  =  algo      & 255;
    out[8]  = (size>>24) & 255;
    out[9]  = (size>>16) & 255;
    out[10] = (size>>8)  & 255;
    out[11] =  size      & 255;
}

int
rice_format(unsigned char algo)
{
    switch (algo) {
        case BCL_ALGO_RICE8S:
            return RICE_FMT_INT8;
        case BCL_ALGO_RICE8:
            return RICE_FMT_UINT8;
        case BCL_ALGO_RICE16S:
            return RICE_FMT_INT16;
        case BCL_ALGO_RICE16:
            return RICE_FMT_UINT16;
        case BCL_ALGO_RICE32S:
            return RICE_FMT_INT32;
        case BCL_ALGO_RICE32:
            return RICE_FMT_UINT32;
        default: // Should never happen.
            return -1;
    }
}

static PyObject *
compress(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *return_value = NULL;
    Py_buffer buffer = {NULL, NULL};
    size_t buflen, outsize, worksize;
    unsigned char *out, algo, format = 0;
    unsigned int newsize, maxcomp, *work = NULL;
    int header = 0;
    bcl_compress_t comp_func;

    static char *keywords[] = {"", "", "header", NULL};

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "y*b|p", keywords, &buffer, &algo, &header)) {
        goto exit;
    }

    buflen = buffer.len;

    if (buflen > UINT_MAX) {
        PyErr_SetString(PyExc_OverflowError,
                        "Buffer length does not fit in an unsigned int");
        goto exit;
    }

    switch (algo) {
        case BCL_ALGO_HUFFMAN:
            comp_func = Huffman_Compress;
            maxcomp = BCL_COMP_MAX_HUFF;
            outsize = BCL_COMP_BUF_HUFF(buflen);
            break;
        case BCL_ALGO_LZ77:
            comp_func = LZ_CompressFast;
            maxcomp = BCL_COMP_MAX_RLE;
            outsize = BCL_COMP_BUF_RLE(buflen);
            worksize = sizeof(unsigned int) * (buflen + 65536);
            if (worksize > UINT_MAX) {
                PyErr_SetString(PyExc_OverflowError,
                                "worksize does not fit in an unsigned int");
                goto exit;
            }
            work = PyMem_Malloc(worksize);
            if (work == NULL) {
                PyErr_NoMemory();
                goto exit;
            }
            break;
        case BCL_ALGO_RICE8:
        case BCL_ALGO_RICE16:
        case BCL_ALGO_RICE32:
        case BCL_ALGO_RICE8S:
        case BCL_ALGO_RICE16S:
        case BCL_ALGO_RICE32S:
            comp_func = (bcl_compress_t)Rice_Compress;
            maxcomp = BCL_COMP_MAX_RICE;
            outsize = BCL_COMP_BUF_RICE(buflen);
            format = rice_format(algo);
            break;
        case BCL_ALGO_RLE:
            comp_func = RLE_Compress;
            maxcomp = BCL_COMP_MAX_RLE;
            outsize = BCL_COMP_BUF_RLE(buflen);
            break;
        case BCL_ALGO_SF:
            comp_func = SF_Compress;
            maxcomp = BCL_COMP_MAX_SF;
            outsize = BCL_COMP_BUF_SF(buflen);
            break;
        default:
            PyErr_Format(BCLError, "Unknown algo %u", algo);
            goto exit;
    }

    if (buflen > (size_t)maxcomp) {
        PyErr_SetString(PyExc_OverflowError,
                        "Cannot compress this amount of bytes");
        goto exit;
    }
    
    if (outsize > UINT_MAX) {
        PyErr_SetString(PyExc_OverflowError,
                        "outsize does not fit in an unsigned int");
        goto exit;
    }
    outsize += header ? BCL_HEADER_SIZE : 0;

    out = PyMem_Calloc(outsize, 1);
    if (out == NULL) {
        PyErr_NoMemory();
        goto exit;
    }

    Py_BEGIN_ALLOW_THREADS
    newsize = comp_func(buffer.buf, header ? &out[BCL_HEADER_SIZE] : out, buffer.len, work, format);
    Py_END_ALLOW_THREADS

    if (header) {
        // The uncompressed data is not larger than UINT_MAX. We should
        // be able to add BCL_HEADER_SIZE to newsize without overflowing.
        newsize += BCL_HEADER_SIZE;
        write_header(out, algo, buflen);
    }

    return_value = PyBytes_FromStringAndSize((const char *)out, newsize);
    PyMem_Free(out);

exit:
    if (buffer.obj) {
       PyBuffer_Release(&buffer);
    }
    PyMem_Free(work);

    return return_value;
}

static PyObject *
decompress(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *return_value = NULL;
    Py_buffer buffer = {NULL, NULL};
    Py_ssize_t outsize = 0;
    size_t buflen;
    int res, header = 0;
    unsigned int hdrsize, newsize;
    unsigned char *in, *out, algo = 0, hdralgo, format = 0;
    bcl_decompress_t decomp_func;

    static char *keywords[] = {"", "algo", "outsize", NULL};

    if (!PyArg_ParseTupleAndKeywords(
            args, kwargs, "y*|bn", keywords, &buffer, &algo, &outsize)) {
        goto exit;
    }

    buflen = buffer.len;

    if (buffer.buf != NULL && buflen > UINT_MAX) {
        PyErr_Format(PyExc_OverflowError,
                     "Compressed data length does not fit in an unsigned int: %zu",
                     buflen);
        goto exit;
    }

    if (buflen >= BCL_HEADER_SIZE) {
        header = read_header(buffer.buf, &hdralgo, &hdrsize) == 0;
    }

    in = buffer.buf;

    if (header) {
        if (algo) {
            if (hdralgo != algo) {
                PyErr_Format(BCLError,
                            "Header's algo %u is different from the requested one %u",
                            hdralgo,
                            algo);
                goto exit;
            }
        }
        else {
            algo = hdralgo;
        }
        in = &in[BCL_HEADER_SIZE];
        buflen -= BCL_HEADER_SIZE;
        outsize = (outsize < 1) ? hdrsize : outsize;
    }
    else if (outsize < 1) {
        PyErr_SetString(BCLError, "Valid outsize required if no header");
        goto exit;
    }

    if (buflen < 1) {
        return_value = PyBytes_FromStringAndSize(NULL, 0);
        goto exit;
    }

    if ((size_t)outsize > UINT_MAX) {
        PyErr_Format(PyExc_OverflowError,
                     "Output buffer size does not fit in an unsigned int: %zd",
                     outsize);
        goto exit;
    }

    switch (algo) {
        case BCL_ALGO_HUFFMAN:
            decomp_func = Huffman_Uncompress;
            break;
        case BCL_ALGO_LZ77:
            decomp_func = LZ_Uncompress;
            break;
        case BCL_ALGO_RLE:
            decomp_func = RLE_Uncompress;
            break;
        case BCL_ALGO_RICE8:
        case BCL_ALGO_RICE16:
        case BCL_ALGO_RICE32:
        case BCL_ALGO_RICE8S:
        case BCL_ALGO_RICE16S:
        case BCL_ALGO_RICE32S:
            decomp_func = (bcl_decompress_t)Rice_Uncompress;
            format = rice_format(algo);
            break;
        case BCL_ALGO_SF:
            decomp_func = SF_Uncompress;
            break;
        default:
            PyErr_Format(BCLError, "Unknown algo %u", algo);
            goto exit;
    }

    out = PyMem_Calloc(outsize, 1);
    if (out == NULL) {
        PyErr_NoMemory();
        goto exit;
    }

    newsize = outsize; // outsize is positive and <= UINT_MAX

    Py_BEGIN_ALLOW_THREADS
    res = decomp_func(in, out, buflen, &newsize, format);
    Py_END_ALLOW_THREADS

    switch (res) {
        case BCL_E_OK:
            return_value = PyBytes_FromStringAndSize((const char *)out, newsize);
            break;
        case BCL_E_INPUT_OVERRUN:
            PyErr_SetString(InputOverrun, "Input overrun");
            break;
        case BCL_E_OUTPUT_OVERRUN:
            PyErr_Format(OutputOverrun,
                        "Output overrun or output buffer too small: %u",
                        newsize);
            break;
        default:
            PyErr_Format(BCLError, "Error %d", res);
    }

    PyMem_Free(out);

exit:
    if (buffer.obj) {
       PyBuffer_Release(&buffer);
    }

    return return_value;
}

static PyMethodDef methods[] = {
    {"compress", _PyCFunction_CAST(compress), METH_VARARGS | METH_KEYWORDS, NULL},
    {"decompress", _PyCFunction_CAST(decompress), METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef bclmodule = {
    PyModuleDef_HEAD_INIT,
    "_bcl",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC
PyInit__bcl(void)
{
    PyObject *module;
    module = PyModule_Create(&bclmodule);
    if (module == NULL) {
        return NULL;
    }
    if (PyModule_AddStringConstant(module, "BCL_MAGIC", BCL_MAGIC)) {
        Py_DECREF(module);
        return NULL;
    }

#define BCL_ADD_INT_MACRO(c)                                 \
    do {                                                     \
        if ((PyModule_AddIntConstant(module, #c, c)) < 0) {  \
            Py_DECREF(module);                               \
            return NULL;                                     \
        }                                                    \
    } while(0)
    
    BCL_ADD_INT_MACRO(BCL_HEADER_SIZE);
    
    BCL_ADD_INT_MACRO(BCL_ALGO_RLE);
    BCL_ADD_INT_MACRO(BCL_ALGO_HUFFMAN);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE8);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE16);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE32);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE8S);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE16S);
    BCL_ADD_INT_MACRO(BCL_ALGO_RICE32S);
    BCL_ADD_INT_MACRO(BCL_ALGO_LZ77);
    BCL_ADD_INT_MACRO(BCL_ALGO_SF);
    
    BCL_ADD_INT_MACRO(RICE_FMT_INT8);
    BCL_ADD_INT_MACRO(RICE_FMT_UINT8);
    BCL_ADD_INT_MACRO(RICE_FMT_INT16);
    BCL_ADD_INT_MACRO(RICE_FMT_UINT16);
    BCL_ADD_INT_MACRO(RICE_FMT_INT32);
    BCL_ADD_INT_MACRO(RICE_FMT_UINT32);

    BCLError = PyErr_NewException("pybcl.BCLError", NULL, NULL);
#if PY_VERSION_HEX >= 0x030a00f0
    if (PyModule_AddObjectRef(module, "BCLError", BCLError) < 0) {
#else
    Py_INCREF(BCLError);
    if (PyModule_AddObject(module, "BCLError", BCLError) < 0) {
        Py_DECREF(BCLError);
#endif
        Py_DECREF(module);
        return NULL;
    }
    
    InputOverrun = PyErr_NewException("pybcl.InputOverrun", BCLError, NULL);
#if PY_VERSION_HEX >= 0x030a00f0
    if (PyModule_AddObjectRef(module, "InputOverrun", InputOverrun) < 0) {
#else
    Py_INCREF(InputOverrun);
    if (PyModule_AddObject(module, "InputOverrun", InputOverrun) < 0) {
        Py_DECREF(InputOverrun);
#endif
        Py_DECREF(module);
        return NULL;
    }
    
    OutputOverrun = PyErr_NewException("pybcl.OutputOverrun", BCLError, NULL);
#if PY_VERSION_HEX >= 0x030a00f0
    if (PyModule_AddObjectRef(module, "OutputOverrun", OutputOverrun) < 0) {
#else
    Py_INCREF(OutputOverrun);
    if (PyModule_AddObject(module, "OutputOverrun", OutputOverrun) < 0) {
        Py_DECREF(OutputOverrun);
#endif
        Py_DECREF(module);
        return NULL;
    }

    return module;
}