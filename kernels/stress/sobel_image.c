/*
 * Sobel gradient adapted from gs_sobel in Grayskull by Serge Zaitsev.
 * https://github.com/zserge/grayskull/blob/main/grayskull.h
 * See LICENSE-Grayskull.txt in this directory for the MIT license.
 *
 * A generated 16x16 grayscale image avoids file I/O and dynamic allocation.
 * The return value is the low 12 bits of a fingerprint of its edge pixels.
 */
#define WIDTH 16u
#define HEIGHT 16u
#define IMAGE_SIZE (WIDTH * HEIGHT)

struct image_buffers {
    unsigned char input[IMAGE_SIZE];
    unsigned char edges[IMAGE_SIZE];
};

static volatile struct image_buffers buffers
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int x, y, i;
    unsigned int fingerprint = 0x13579bdfu;

    for (y = 0; y < HEIGHT; ++y) {
        for (x = 0; x < WIDTH; ++x) {
            buffers.input[y * WIDTH + x] = (unsigned char)
                (13u * x + 17u * y + ((x ^ y) << 3) + (x > y ? 37u : 0u));
            buffers.edges[y * WIDTH + x] = 0;
        }
    }

    /* Borders remain zero, matching Grayskull's interior-only Sobel loop. */
    for (y = 1; y < HEIGHT - 1; ++y) {
        for (x = 1; x < WIDTH - 1; ++x) {
            unsigned int p = y * WIDTH + x;
            int a = buffers.input[p - WIDTH - 1];
            int b = buffers.input[p - WIDTH];
            int c = buffers.input[p - WIDTH + 1];
            int d = buffers.input[p - 1];
            int f = buffers.input[p + 1];
            int g = buffers.input[p + WIDTH - 1];
            int h = buffers.input[p + WIDTH];
            int j = buffers.input[p + WIDTH + 1];
            int gx = -a + c - 2 * d + 2 * f - g + j;
            int gy = -a - 2 * b - c + g + 2 * h + j;
            int magnitude = ((gx < 0 ? -gx : gx) + (gy < 0 ? -gy : gy)) / 2;
            buffers.edges[p] = (unsigned char)(magnitude > 255 ? 255 : magnitude);
        }
    }

    for (i = 0; i < IMAGE_SIZE; ++i) {
        fingerprint = ((fingerprint << 5) | (fingerprint >> 27)) ^ buffers.edges[i];
    }
    return (int)(fingerprint & 0xfffu);
}
