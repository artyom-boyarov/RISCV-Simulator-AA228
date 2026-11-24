#include "../error_codes.h"

/* Link .memory_region at 0x000; volatile preserves the sparse accesses. */
#define PAGE_SIZE 4096u
#define STRIDE 16u

volatile unsigned char memory_region[PAGE_SIZE]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int i;
    // 0x000 = 0
    // 0x010 = 1
    // 0xFF0 = 0xFF
    for (i = 0; i < PAGE_SIZE / STRIDE; ++i)
        memory_region[i * STRIDE] = (unsigned char)i;

    // 0x000 = 0
    // 0x010 = 1
    for (i = 0; i < PAGE_SIZE / STRIDE; ++i) {
        if (memory_region[i * STRIDE] != (unsigned char)i)
            return KERNEL_FAILURE(i * STRIDE);
    }
    return KERNEL_SUCCESS;
}
