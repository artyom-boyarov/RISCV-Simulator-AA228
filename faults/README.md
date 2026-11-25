# Example fault configurations

Pass a file to the simulator with `-f`, for example:

```sh
./compile-riscv.sh kernels/fault-detection/memory_stride_kernel.c
./build/Simulator kernels/bin/memory_stride_kernel.riscv -q --no-cache \
  -f faults/memory/bit11-stuck-at-0-100.txt
```

The branch predictor files invert 50% or 100% of branch predictions.
`memory/` covers all combinations of page-offset bits 0–11, the three fault
types, and 50% or 100% rates. Run
`python3 faults/generate_memory_faults.py` to create missing files.
Memory faults are suppressed during instruction fetches
but can affect data and stack accesses, so a fault can still prevent a program
from reaching its return statement.

`cache/` contains every combination of L1 metadata field, meaningful bit,
fault type, and 50% or 100% rate for the current 1 KiB, 64-byte-line, 8-way
cache: valid and modified bit 0, set ID bit 0, and tag bits 0–24. For example:

```sh
./build/Simulator kernels/bin/memory_page_kernel.riscv -q \
  -f faults/cache/tag-bit00-stuck-at-0-100.txt
```

Do not use `--no-cache` when testing a cache fault. Faults affect metadata
reads across all L1 blocks, and are suppressed during instruction fetches.
The files can be regenerated with `python3 faults/generate_cache_faults.py`;
update its field widths if the L1 geometry changes.
