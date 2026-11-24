#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
gcc=${RISCV_GCC:-$HOME/riscv64i/bin/riscv64-unknown-elf-gcc}
objdump=${RISCV_OBJDUMP:-$HOME/riscv64i/bin/riscv64-unknown-elf-objdump}
mkdir -p "$root/kernels/bin/inclass" "$root/kernels/assembly/inclass"
for name in add double-float mul-div 'n!' qsort simple-function; do
    "$gcc" -march=rv64i "$root/kernels/smoke/inclass/$name.c" -o "$root/kernels/bin/inclass/$name.riscv"
    "$objdump" -D "$root/kernels/bin/inclass/$name.riscv" > "$root/kernels/assembly/inclass/$name.s"
done
