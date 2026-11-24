#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cmake -S "$root" -B "$root/build"
cmake --build "$root/build"
for name in add mul-div 'n!' qsort simple-function; do
    "$root/build/Simulator" "$root/kernels/bin/inclass/$name.riscv"
done
