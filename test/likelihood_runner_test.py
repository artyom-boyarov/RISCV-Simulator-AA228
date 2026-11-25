import csv
import os
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    import numpy as np
except ImportError:
    print("NumPy is not installed; skipping likelihood runner test")
    sys.exit(77)

root = Path(__file__).resolve().parents[1]
runner = root / "generate_likelihoods.py"

with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    simulator = temp / "simulator"
    simulator.write_text("""#!/usr/bin/env python3
import pathlib, sys, time
args = sys.argv[1:]
kernel = pathlib.Path(args[0]).name
config = pathlib.Path(args[args.index('-f') + 1]).read_text() if '-f' in args else ''
pathlib.Path('dump.txt').write_text(kernel)
if 'field = valid' in config and kernel == 'fail.riscv':
    sys.exit(7)
if 'type = branch' in config and kernel == 'fail.riscv':
    time.sleep(2)
print('Program return value:')
print(2 if 'field = valid' in config else 0)
""")
    simulator.chmod(0o755)
    good, fail = temp / "good.riscv", temp / "fail.riscv"
    good.touch()
    fail.touch()
    cache, branch = temp / "cache.txt", temp / "branch.txt"
    cache.write_text("type = cache\nfield = valid\nbit = 0\nfault = STUCK_AT_0\nrate = 1\n")
    branch.write_text("type = branch\nrate = 0.5\n")
    campaign = temp / "campaign"

    def call(*args, check=True):
        result = subprocess.run([sys.executable, str(runner), *map(str, args)],
                                cwd=temp, text=True, capture_output=True)
        if check and result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return result

    call("prepare", campaign, "--simulator", simulator, "--kernel", good, "--kernel", fail,
         "--fault", cache, "--fault", branch, "--runs", "2", "--timeout", "0.5")
    assert "Missing" in call("aggregate", campaign, check=False).stderr
    call("run-state", campaign, "0")
    call("run", campaign, "--processes", "2")  # resumes the remaining states
    call("aggregate", campaign)
    with (campaign / "states.csv").open() as f:
        states = list(csv.DictReader(f))
    assert len(states) == 3 and states[0]["name"].endswith("cache.txt") and states[-1]["name"] == "no_fault"
    with np.load(campaign / "likelihoods.npz", allow_pickle=False) as data:
        labels = list(data["outcome_labels"])
        assert data["L"].shape == (2, 3, len(labels))
        np.testing.assert_allclose(data["L"].sum(axis=2), 1)
        assert data["counts"][0, 0, labels.index("return:2")] == 2
        assert data["counts"][1, 0, labels.index("exit:7")] == 2
        assert data["counts"][1, 1, labels.index("timeout")] == 2
        assert data["counts"][1, 2, labels.index("return:0")] == 2
        assert data["seconds"].shape == (2, 3, 2)
    assert call("run-state", campaign, "0", check=False).returncode != 0

    batch = temp / "batch"
    call("batch", batch, "--simulator", simulator, "--kernel", good, "--kernel", fail,
         "--fault", cache, "--fault", branch, "--runs", "1", "--timeout", "0.5",
         "--processes", "1")
    assert (batch / "likelihoods.npz").is_file()
    pids = []
    for state in range(3):
        with np.load(batch / "states" / f"{state:04d}.npz", allow_pickle=False) as data:
            pids.append(int(data["worker_pid"]))
    assert len(set(pids)) == 3, pids

