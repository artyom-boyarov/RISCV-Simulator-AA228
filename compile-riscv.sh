#!/usr/bin/env bash
set -euo pipefail

if (( $# < 1 || $# > 2 )); then
    echo "Usage: $0 source.c [output.riscv]" >&2
    exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_file=$1
output_file=${2:-$script_dir/kernels/bin/$(basename -- "${source_file%.c}").riscv}

if [[ ! -f "$source_file" || "$source_file" != *.c ]]; then
    echo "Expected an existing C source file: $source_file" >&2
    exit 1
fi
if [[ "$source_file" -ef "$output_file" ]]; then
    echo "Output must differ from the source file" >&2
    exit 1
fi

source_dir=$(cd -- "$(dirname -- "$source_file")" && pwd)
extra_sources=()
extra_flags=()
if [[ "$source_dir" == "$script_dir/kernels/smoke/test" && "$(basename -- "$source_file")" != lib.c ]]; then
    extra_sources+=("$script_dir/kernels/smoke/test/lib.c")
fi
if [[ "$source_dir" == "$script_dir/kernels/fault-detection" ||
      "$source_dir" == "$script_dir/kernels/stress" ]]; then
    extra_flags+=(-O1)
fi
if [[ "$source_dir" == "$script_dir/kernels/fault-detection" &&
      "$(basename -- "$source_file")" == cache_tag_bits_kernel.c ]]; then
    extra_sources+=("$script_dir/kernels/fault-detection/cache_tag_bit_regions.S")
    # The low bit-9 probe shares the code page, and the bit-24 probes use
    # stack pages initialized by the simulator. The other probes need ELF sections.
    for ((bit = 0; bit < 25; ++bit)); do
        if (( bit != 9 && bit != 24 )); then
            printf -v address '%x' "$((1 << (bit + 7)))"
            extra_flags+=("-Wl,--section-start=.taglow$bit=0x$address")
        fi
        if (( bit != 24 )); then
            printf -v address '%x' "$((0xffffff80 ^ (1 << (bit + 7))))"
            extra_flags+=("-Wl,--section-start=.taghigh$bit=0x$address")
        fi
    done
    extra_flags+=(-Wl,--section-start=.taghighref=0xffffff80)
fi
mkdir -p -- "$(dirname -- "$output_file")"
"${RISCV_GCC:-riscv64-unknown-elf-gcc}" \
    -march=rv64i -mabi=lp64 -ffreestanding -nostdlib -static \
    "${extra_flags[@]}" -Wl,-e,_start -Wl,--no-relax -Wl,--section-start=.memory_region=0x0 \
    "$script_dir/kernels/start.S" "$source_file" "${extra_sources[@]}" -o "$output_file"
echo "Built $output_file"
