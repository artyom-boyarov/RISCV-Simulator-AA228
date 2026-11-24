#include "../error_codes.h"

/* Link this entire page at 0x000. */
#define PAGE_BASE 0x000u
#define PAGE_SIZE 4096u
#define OFFSET_MASK (PAGE_SIZE - 1u)
#define OFFSET_BITS 12u

volatile unsigned char memory_region[PAGE_SIZE]
    __attribute__((section(".memory_region"), aligned(1), used));

static int test_pair(unsigned int first, unsigned int second) {
    memory_region[first] = 0xfeu;
    memory_region[second] = 0xefu;
    if (memory_region[first] != 0xfeu)
        return KERNEL_FAILURE(PAGE_BASE + first);
    if (memory_region[second] != 0xefu)
        return KERNEL_FAILURE(PAGE_BASE + second);
    return KERNEL_SUCCESS;
}

int main(void) {
    unsigned int bit;
    int result;

    for (bit = 0; bit < OFFSET_BITS; ++bit) {
        result = test_pair(OFFSET_MASK, OFFSET_MASK ^ (1u << bit));
        if (result != KERNEL_SUCCESS) return result;
    }
    for (bit = 0; bit < OFFSET_BITS; ++bit) {
        result = test_pair(0, 1u << bit);
        if (result != KERNEL_SUCCESS) return result;
    }
    return KERNEL_SUCCESS;
}
