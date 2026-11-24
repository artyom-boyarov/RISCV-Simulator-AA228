# RISC-V guest programs

- `smoke/test/`: original test programs and their `lib.c` syscall helpers.
- `smoke/inclass/`: original in-class programs.
- `fault-detection/`: memory test kernels.
- `stress/`: small numerical workloads, including an integer Sobel image filter.
- `start.S`: minimal startup shared by the freestanding builds.
- `error_codes.h`: shared success sentinel and legacy encoded-error helpers.
- `bin/test/` and `bin/inclass/`: original reference ELF executables.
- `assembly/`: corresponding reference disassemblies.
- `bin/`: default destination for new builds.

From the repository root, compile and run a guest program with:

```sh
./compile-riscv.sh kernels/fault-detection/memory_stride_kernel.c
./build/Simulator kernels/bin/memory_stride_kernel.riscv -q --no-cache
```

The build script automatically links `smoke/test/lib.c` for programs in that
directory, and places a `.memory_region` section at `0x000` when present.
The legacy batch build scripts require a cross-toolchain with its C runtime and
libraries; the freestanding script needs only GCC and binutils.

Fault-detection kernels return the first failing address plus one, except
`cache_tag_bits_kernel.c`, which returns the detected tag bit number plus one.
All return `KERNEL_SUCCESS` (`0`) on success. Subtract one from a nonzero
result to recover the address or bit number.
