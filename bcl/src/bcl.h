#define BCL_MAGIC "BCL1"
#define BCL_HEADER_SIZE 12

#define BCL_ALGO_RLE     1
#define BCL_ALGO_HUFFMAN 2
#define BCL_ALGO_RICE8   3
#define BCL_ALGO_RICE16  4
#define BCL_ALGO_RICE32  5
#define BCL_ALGO_RICE8S  6
#define BCL_ALGO_RICE16S 7
#define BCL_ALGO_RICE32S 8
#define BCL_ALGO_LZ77    9
#define BCL_ALGO_SF      10

#define BCL_E_OK             0
#define BCL_E_ERROR          (-1)
#define BCL_E_INPUT_OVERRUN  (-4)
#define BCL_E_OUTPUT_OVERRUN (-5)

#define BCL_COMP_BUF_HUFF(insize) ((insize) * (101.0 / 100.0) + 320)
#define BCL_COMP_BUF_RICE(insize) ((insize) + 1)
#define BCL_COMP_BUF_RLE(insize)  ((insize) * (257.0 / 256.0) + 1)
#define BCL_COMP_BUF_SF(insize)   ((insize) * (101.0 / 100.0) + 384)

#define BCL_COMP_MAX_HUFF (unsigned int)((UINT_MAX - 320) / (101.0 / 100.0))
#define BCL_COMP_MAX_RICE (UINT_MAX - 1)
#define BCL_COMP_MAX_RLE  (unsigned int)((UINT_MAX - 1)   / (257.0 / 256.0))
#define BCL_COMP_MAX_SF   (unsigned int)((UINT_MAX - 384) / (101.0 / 100.0))

typedef int (*bcl_compress_t)  (unsigned char *in,     unsigned char *out,
                                unsigned int   insize, unsigned int  *work,
                                int format);
typedef int (*bcl_decompress_t)(unsigned char *in,     unsigned char *out,
                                unsigned int   insize, unsigned int  *outsize,
                                int format);