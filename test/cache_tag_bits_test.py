import os
import pathlib
import re
import subprocess
import sys
import tempfile

compiler, simulator, root_arg = sys.argv[1:]
root = pathlib.Path(root_arg)
with tempfile.TemporaryDirectory() as directory:
    elf = pathlib.Path(directory) / "cache_tag_bits.riscv"
    env = dict(os.environ, RISCV_GCC=compiler)
    subprocess.run([str(root / "compile-riscv.sh"),
                    str(root / "kernels/fault-detection/cache_tag_bits_kernel.c"),
                    str(elf)], check=True, env=env, cwd=directory)

    def run(fault=None):
        args = [simulator, str(elf), "-q"]
        if fault:
            args += ["-f", str(fault)]
        result = subprocess.run(args, cwd=directory, text=True, capture_output=True,
                                timeout=30)
        assert result.returncode == 0, result.stderr[-2000:]
        match = re.search(r"Program return value:\s*(-?\d+)", result.stdout)
        assert match, result.stdout
        return int(match.group(1))

    assert run() == 0
    for bit in range(25):
        for stuck in (0, 1):
            fault = root / f"faults/cache/tag-bit{bit:02d}-stuck-at-{stuck}-100.txt"
            assert run(fault) == bit + 1, (bit, stuck)
