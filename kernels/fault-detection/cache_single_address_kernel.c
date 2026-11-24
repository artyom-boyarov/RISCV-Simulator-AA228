#include "../error_codes.h"

#define TEST_ADDRESS 0x000u
#define TEST_SIZE 4096u

/* The linker places this page at TEST_ADDRESS. */
volatile unsigned char cache_test_region[TEST_SIZE]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int offset, value;
    for (offset = 0; offset < TEST_SIZE; ++offset) {
        for (value = 0; value < 16; ++value)
            cache_test_region[offset] = (unsigned char)value;
        if (cache_test_region[offset] != 15u)
            return KERNEL_FAILURE(TEST_ADDRESS + offset);
    }
    return KERNEL_SUCCESS;
}
