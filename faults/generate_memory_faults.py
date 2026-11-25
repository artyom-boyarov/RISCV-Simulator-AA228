#!/usr/bin/env python3
"""Generate missing offset-bit 0–11 memory fault configurations."""

from pathlib import Path

root = Path(__file__).resolve().parent
output = root / "memory"
output.mkdir(exist_ok=True)


def memory_fault(path):
    properties = {}
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        properties[key] = value
    if properties.get("type") != "memory":
        return None
    fault = properties["fault"]
    rate = float(properties.get("rate", 0.5 if fault == "BIT_FLIP" else 1.0))
    return int(properties["bit"]), fault, rate


# Avoid duplicate configurations by checking their contents.
existing = {fault for path in root.rglob("*.txt")
            if (fault := memory_fault(path)) is not None}
for bit in range(12):
    for fault in ("STUCK_AT_0", "STUCK_AT_1", "BIT_FLIP"):
        for rate in (1.0, 0.5):
            if (bit, fault, rate) in existing:
                continue
            rate_label = "100" if rate == 1.0 else "50"
            filename = f"bit{bit:02d}-{fault.lower().replace('_', '-')}-{rate_label}.txt"
            path = output / filename
            if path.exists():
                raise FileExistsError(f"Refusing to overwrite {path}")
            path.write_text(f"type = memory\nfault = {fault}\nbit = {bit}\nrate = {rate}\n")
            existing.add((bit, fault, rate))
