#include "../error_codes.h"

/* L1: 64-byte lines, two sets, eight ways. All these offsets share a set. */
#define TEST_ADDRESS 0x000u
#define SET_STRIDE 128u
#define L1_WAYS 8u
#define TEST_VALUE 0xa5u

volatile unsigned char cache_test_region[L1_WAYS * SET_STRIDE + 1u]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int i;

    cache_test_region[0] = TEST_VALUE;
    for (i = 1; i <= L1_WAYS; ++i)
        (void)cache_test_region[i * SET_STRIDE];

    if (cache_test_region[0] != TEST_VALUE)
        return KERNEL_FAILURE(TEST_ADDRESS);
    return KERNEL_SUCCESS;
}
