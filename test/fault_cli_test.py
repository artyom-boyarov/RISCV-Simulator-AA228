import pathlib
import re
import subprocess
import sys
import tempfile

simulator, elf = sys.argv[1:]

with tempfile.TemporaryDirectory() as directory:
    config = pathlib.Path(directory) / "faults.txt"

    def run(contents, binary=elf, extra=()):
        config.write_text(contents)
        return subprocess.run([simulator, binary, "-b", "NT", "-f", str(config), *extra],
                              cwd=directory, text=True, capture_output=True, timeout=30)

    baseline = subprocess.run([simulator, elf, "-b", "NT"], cwd=directory,
                              text=True, capture_output=True, timeout=30)
    flipped = run("# invert every prediction\ntype = branch\nrate = 1\n")
    assert baseline.returncode == 0 and flipped.returncode == 0, (baseline.stderr, flipped.stderr)
    pattern = r"Branch Perdiction Accuacy: ([0-9.]+)"
    before = float(re.search(pattern, baseline.stdout).group(1))
    after = float(re.search(pattern, flipped.stdout).group(1))
    assert abs(before + after - 1) < 0.001, (before, after)
    repeated = run("type = branch\nrate = 0.5\nignored = value\nrate = 1\n")
    assert repeated.returncode == 0 and float(re.search(pattern, repeated.stdout).group(1)) == after

    # Verify that a combined file parses before ELF loading.
    combined = """type = memory
fault = STUCK_AT_0
bit = 11
type = cache
field = valid
fault = BIT_FLIP
bit = 0
type = branch
rate = 0.5
"""
    result = run(combined, binary=str(pathlib.Path(directory) / "missing.elf"))
    assert "Fail to load ELF" in result.stderr and "Fault configuration error" not in result.stderr
    unchecked = run("type = memory\nfault = BIT_FLIP\nbit = 12\n",
                    binary=str(pathlib.Path(directory) / "missing.elf"))
    assert "Fail to load ELF" in unchecked.stderr and "Fault configuration error" not in unchecked.stderr
    result = run(combined.replace("type = cache\n", "type = cache\nlevel = L1\n"),
                 binary=str(pathlib.Path(directory) / "missing.elf"))
    assert "Fail to load ELF" in result.stderr and "Fault configuration error" not in result.stderr

    invalid = [
        ("rate = 0.5\n", "first property must be type"),
        ("type = memory\nfault = BIT_FLIP\n", "missing property"),
        ("type = branch\nrate = 0.3\n", "rate must be 0.5 or 1.0"),
        ("type = memory\nfault = BIT_FLIP\nbit = 3\nrate = 0\n", "rate must be 0.5 or 1.0"),
        ("type = cache\nfield = tag\nfault = STUCK_AT_0\nbit = 0\nrate = 0.7\n", "rate must be 0.5 or 1.0"),
    ]
    for contents, expected in invalid:
        result = run(contents)
        assert result.returncode != 0 and expected in result.stderr, (contents, result.stderr)
        assert str(config) in result.stderr
