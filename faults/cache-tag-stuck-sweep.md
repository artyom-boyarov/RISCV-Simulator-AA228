# L1 tag stuck-at fault sweep

Historical results: these runs used kernels based at `0x1000`, before the
fault-detection kernels were moved to `0x000`. Results may differ now.

The simulator was run once for each combination of tag bit 1–24, stuck value
0 or 1, and three existing memory kernel binaries. Each fault used a 100% rate,
cache was enabled, and instruction-fetch fault suppression was active. All 144
runs exited normally; none timed out. The current L1 has a 1 KiB capacity,
64-byte blocks, and eight ways.

Each cell lists bit positions grouped by guest return value. `0` means the
kernel reported success; a nonzero result is `(first failing address << 2) | 1`.

| Kernel | Fault | Result | Tag bits |
| --- | --- | --- | --- |
| 256-byte | stuck 0 | `0x4005` (address `0x1001`) | 5 |
| 256-byte | stuck 0 | 0 | 1–4, 6–24 |
| 256-byte | stuck 1 | `0x4005` (address `0x1001`) | 1–4, 6–24 |
| 256-byte | stuck 1 | 0 | 5 |
| Full page | stuck 0 | `0x4005` (address `0x1001`) | 1–5 |
| Full page | stuck 0 | 0 | 6–24 |
| Full page | stuck 1 | `0x4005` (address `0x1001`) | 1–4, 6–24 |
| Full page | stuck 1 | 0 | 5 |
| Address-bit | stuck 0 | `0x7ffd` (address `0x1fff`) | 1–5 |
| Address-bit | stuck 0 | 0 | 6–24 |
| Address-bit | stuck 1 | `0x7bfd` (address `0x1eff`) | 1 |
| Address-bit | stuck 1 | `0x77fd` (address `0x1dff`) | 2 |
| Address-bit | stuck 1 | `0x6ffd` (address `0x1bff`) | 3 |
| Address-bit | stuck 1 | `0x5ffd` (address `0x17ff`) | 4 |
| Address-bit | stuck 1 | 0 | 5 |
| Address-bit | stuck 1 | `0x7ffd` (address `0x1fff`) | 6–24 |

Example invocation:

```sh
./build/Simulator kernels/bin/memory_page_kernel.riscv -q \
  -f faults/cache/tag-bit05-stuck-at-0-100.txt
```

These are observations of this implementation and workload, not a proof of
fault coverage. A success result can mean the fault did not affect the values
the kernel checked. Tag faults apply to all L1 blocks, including stack data.
