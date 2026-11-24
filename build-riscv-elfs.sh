#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
gcc=${RISCV_GCC:-$HOME/riscv64i/bin/riscv64-unknown-elf-gcc}
objdump=${RISCV_OBJDUMP:-$HOME/riscv64i/bin/riscv64-unknown-elf-objdump}
mkdir -p "$root/kernels/bin/test" "$root/kernels/assembly/test"
for name in helloworld test_arithmetic test_syscall test_branch quicksort matrixmulti ackermann; do
    "$gcc" -march=rv64i "$root/kernels/smoke/test/$name.c" "$root/kernels/smoke/test/lib.c" -o "$root/kernels/bin/test/$name.riscv"
    "$objdump" -D "$root/kernels/bin/test/$name.riscv" > "$root/kernels/assembly/test/$name.s"
done
