#include "../error_codes.h"

/* Link .memory_region at 0x000; volatile preserves all memory accesses. */
#define REGION_SIZE 256u
#define REGIONS 16u

volatile unsigned char memory_region[REGION_SIZE * REGIONS]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int region, index, offset;

    for (region = 0; region < REGIONS; ++region) {
        for (index = 0; index < REGION_SIZE; ++index) {
            offset = region * REGION_SIZE + index;
            memory_region[offset] = (unsigned char)offset;
        }
    }
    for (region = 0; region < REGIONS; ++region) {
        for (index = 0; index < REGION_SIZE; ++index) {
            offset = region * REGION_SIZE + index;
            if (memory_region[offset] != (unsigned char)offset)
                return KERNEL_FAILURE(offset);
        }
    }
    return KERNEL_SUCCESS;
}
