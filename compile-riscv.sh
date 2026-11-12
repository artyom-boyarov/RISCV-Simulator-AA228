#!/usr/bin/env bash
set -euo pipefail

if (( $# < 1 || $# > 2 )); then
    echo "Usage: $0 source.c [output.riscv]" >&2
    exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_file=$1
output_file=${2:-${source_file%.c}.riscv}

if [[ ! -f "$source_file" || "$source_file" != *.c ]]; then
    echo "Expected an existing C source file: $source_file" >&2
    exit 1
fi
if [[ "$source_file" -ef "$output_file" ]]; then
    echo "Output must differ from the source file" >&2
    exit 1
fi

"${RISCV_GCC:-riscv64-unknown-elf-gcc}" \
    -march=rv64i -mabi=lp64 -O0 -ffreestanding -nostdlib -static \
    -Wl,-e,_start "$script_dir/test/start.S" "$source_file" -o "$output_file"
echo "Built $output_file"
