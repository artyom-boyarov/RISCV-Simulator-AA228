#ifndef KERNEL_ERROR_CODES_H
#define KERNEL_ERROR_CODES_H

/* The low two bits identify the error; zero is reserved for no error. */
#define ERR_TYPE_NONE 0u
#define ERR_TYPE_DATA_INVALID 1u
#define ERR_TYPE_MASK 3u

/* E_VAL must fit in 30 bits; ERR_TYPE must fit in two bits. */
#define ERROR_CODE(E_VAL, ERR_TYPE) \
    (((unsigned int)(E_VAL) << 2) | (unsigned int)(ERR_TYPE))

#endif
