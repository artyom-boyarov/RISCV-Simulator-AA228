#include "../error_codes.h"

/* Link .memory_region at 0x1000; volatile preserves the sparse accesses. */
#define PAGE_SIZE 4096u
#define STRIDE 16u

volatile unsigned char memory_region[PAGE_SIZE]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int i;

    for (i = 0; i < PAGE_SIZE / STRIDE; ++i)
        memory_region[i * STRIDE] = (unsigned char)i;

    for (i = 0; i < PAGE_SIZE / STRIDE; ++i) {
        if (memory_region[i * STRIDE] != (unsigned char)i)
            return (int)ERROR_CODE(0x1000u + i * STRIDE, ERR_TYPE_DATA_INVALID);
    }
    return 0;
}
