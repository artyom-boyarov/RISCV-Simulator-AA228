#include "../error_codes.h"

/* The linker places this region at 0x1000; volatile forces every access. */
#define REGION_SIZE 256u
#define SWEEPS 16u

volatile unsigned char memory_region[REGION_SIZE]
    __attribute__((section(".memory_region"), aligned(1), used));

int main(void) {
    unsigned int offset;
    unsigned int sweep;

    for (offset = 0; offset < REGION_SIZE; ++offset)
        memory_region[offset] = (unsigned char)offset;

    for (sweep = 0; sweep < SWEEPS; ++sweep) {
        for (offset = 0; offset < REGION_SIZE; ++offset) {
            if (memory_region[offset] != (unsigned char)offset)
                return (int)ERROR_CODE(0x1000u + offset, ERR_TYPE_DATA_INVALID);
        }
    }
    return 0;
}
