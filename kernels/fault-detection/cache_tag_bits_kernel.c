#include "../error_codes.h"

/* The current L1 has 6 line-offset bits and 1 set-index bit. */
#define TAG_SHIFT 7u
#define TAG_BITS 25u
#define HIGH_TAG_ADDRESS 0xffffff80u

/* Link at zero; the accompanying ELF sections map the sparse probe addresses. */
volatile unsigned char zero_tag
    __attribute__((section(".memory_region"), used));

int main(void) {
    unsigned int bit;
    unsigned int reference_address;
    volatile unsigned char *reference;

    /* A stuck-one fault makes a zero-tag line fail an immediate write/read. */
    zero_tag = 0x53u;
    if (zero_tag == 0x53u) {
        reference_address = 0;
        reference = &zero_tag;
    } else {
        reference_address = HIGH_TAG_ADDRESS;
        reference = (volatile unsigned char *)(unsigned long)reference_address;
    }

    for (bit = 0; bit < TAG_BITS; ++bit) {
        unsigned int address = reference_address ^ (1u << (TAG_SHIFT + bit));
        volatile unsigned char *other =
            (volatile unsigned char *)(unsigned long)address;
        *reference = 0x35u;
        *other = 0xc6u;
        if (*reference != 0x35u || *other != 0xc6u)
            return KERNEL_FAILURE(bit);
    }
    return KERNEL_SUCCESS;
}
