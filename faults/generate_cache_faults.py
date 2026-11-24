#!/usr/bin/env python3
"""Generate the L1 metadata faults for the simulator's current cache geometry."""

from pathlib import Path

# 1 KiB L1, 64-byte lines, 8-way: 6 offset bits, 1 set bit, 25 tag bits.
FIELD_WIDTHS = {"valid": 1, "modified": 1, "id": 1, "tag": 25}
FAULT_TYPES = ("STUCK_AT_0", "STUCK_AT_1", "BIT_FLIP")
RATES = ("0.5", "1.0")

output = Path(__file__).resolve().parent / "cache"
output.mkdir(exist_ok=True)
for field, width in FIELD_WIDTHS.items():
    for bit in range(width):
        for fault in FAULT_TYPES:
            for rate in RATES:
                label = "50" if rate == "0.5" else "100"
                path = output / f"{field}-bit{bit:02d}-{fault.lower().replace('_', '-')}-{label}.txt"
                path.write_text(f"type = cache\nfield = {field}\nbit = {bit}\n"
                                f"fault = {fault}\nrate = {rate}\n")
