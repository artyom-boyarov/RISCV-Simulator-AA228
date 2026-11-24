# RISC-V guest programs

- `smoke/test/`: original test programs and their `lib.c` syscall helpers.
- `smoke/inclass/`: original in-class programs.
- `fault-detection/`: memory test kernels.
- `start.S`: minimal startup shared by the freestanding builds.
- `error_codes.h`: shared error types and `ERROR_CODE(value, type)` encoding.
- `bin/test/` and `bin/inclass/`: original reference ELF executables.
- `assembly/`: corresponding reference disassemblies.
- `bin/`: default destination for new builds.

From the repository root, compile and run a guest program with:

```sh
./compile-riscv.sh kernels/fault-detection/memory_stride_kernel.c
./build/Simulator kernels/bin/memory_stride_kernel.riscv -q --no-cache
```

The build script automatically links `smoke/test/lib.c` for programs in that
directory, and places a `.memory_region` section at `0x1000` when present.
The legacy batch build scripts require a cross-toolchain with its C runtime and
libraries; the freestanding script needs only GCC and binutils.

Fault-detection kernels return `ERROR_CODE(address, ERR_TYPE_DATA_INVALID)` on
the first mismatch, and return 0 for success. The encoded value places the
error type in the low two bits; `ERR_TYPE_MASK` can extract them. Values must
fit in 30 bits and error types in two bits.
