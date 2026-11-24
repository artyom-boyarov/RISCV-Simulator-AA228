# L1 cache fault experiment

Historical results: these runs used kernels based at `0x1000`, before the
fault-detection kernels were moved to `0x000`. Results may differ now.

These runs used the checked-in memory kernel binaries, the 1 KiB L1 cache with
64-byte lines and 8-way associativity, and `-q` with cache enabled. Each fault
was configured at rate `1.0`. A zero is the guest return value, not a host
process status. A nonzero value encodes `(first_mismatching_address << 2) | 1`.

| L1 fault | 256-byte kernel | Full-page kernel | Address-bit kernel |
| --- | ---: | ---: | ---: |
| None | 0 | 0 | 0 |
| Valid bit 0 stuck at 0 | `0x4005` (`0x1001`) | `0x4005` (`0x1001`) | `0x7ffd` (`0x1fff`) |
| Valid bit 0 stuck at 1 | 0 | 0 | 0 |
| Modified bit 0 stuck at 0 | 0 | `0x4005` (`0x1001`) | 0 |
| Tag bit 0 stuck at 0 | `0x4005` (`0x1001`) | `0x4005` (`0x1001`) | `0x7ffd` (`0x1fff`) |
| Tag bit 0 flipped | `0x4005` (`0x1001`) | `0x4005` (`0x1001`) | `0x7ffd` (`0x1fff`) |
| ID bit 0 stuck at 0 | `0x4101` (`0x1040`) | `0x4101` (`0x1040`) | `0x7ffd` (`0x1fff`) |

One run was performed for each cell. The examples are deterministic at 100%;
they are observations of this simulator and workload, not a general coverage
claim. A zero result does not prove that the fault had no effect. Instruction
fetches suppress fault injection, but cache effects from data and stack accesses
remain active. 50% faults can vary from one run to another.
