import json
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    import numpy as np
except ImportError:
    sys.exit(77)

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from generate_likelihoods import checksum
from random_guessing import select_state
import random

assert all(select_state(None, ["no_fault", "fault"], random.Random(seed)) == 1
           for seed in range(20))
assert select_state("no_fault", ["no_fault", "fault"], random.Random(0)) == 0

with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    simulator = temp / "simulator"
    simulator.write_text("""#!/usr/bin/env python3
import pathlib, sys
args = sys.argv[1:]
fault = pathlib.Path(args[args.index('-f') + 1]).read_text()
print('Program return value:')
print(9 if fault == 'zero evidence' else 1)
""")
    simulator.chmod(0o755)
    kernel = temp / "kernel.riscv"
    kernel.touch()
    campaign = temp / "campaign"
    (campaign / "configs").mkdir(parents=True)
    for index, content in enumerate(("known", "zero evidence")):
        (campaign / "configs" / f"{index}.txt").write_text(content)
    states = [{"index": i, "name": f"state-{i}", "config": f"configs/{i}.txt",
               "config_sha256": checksum(campaign / "configs" / f"{i}.txt")}
              for i in range(2)]
    manifest = {"simulator_sha256": checksum(simulator), "branch_strategy": "NT", "timeout_seconds": 2,
                "tests": [{"name": "kernel", "path": str(kernel), "sha256": checksum(kernel), "no_cache": False}],
                "states": states}
    (campaign / "manifest.json").write_text(json.dumps(manifest))

    def likelihoods(array):
        np.savez(campaign / "likelihoods.npz", L=np.asarray([array]),
                 test_names=np.asarray(["kernel"]), state_names=np.asarray(["state-0", "state-1"]),
                 outcome_labels=np.asarray(["return:0", "return:1", "return:9"]))

    def run(state):
        return subprocess.run([sys.executable, str(root / "experiment_belief.py"), str(campaign),
                               "--simulator", str(simulator), "--state", str(state),
                               "--seed", "42", "--max-steps", "4"], text=True, capture_output=True)

    likelihoods([[0.1, 0.9, 0], [0.9, 0.1, 0]])
    result = run(0)
    assert result.returncode == 0, result.stderr
    assert "Stopped after 2 tests" in result.stdout and "correct diagnosis" in result.stdout
    assert "P=0.900000" in result.stdout  # Equal to 0.9 must not stop the experiment.
    result = run(1)
    assert result.returncode == 2 and "zero likelihood" in result.stderr

    likelihoods([[1.0, 0, 0], [0, 1.0, 0]])
    result = run(0)
    assert result.returncode == 0 and "incorrect diagnosis" in result.stdout
    assert "eliminate" in result.stderr

    likelihoods([[0.1, 0.9, 0], [0.1, 0.9, 0]])
    result = run(0)
    assert result.returncode == 1 and "without exceeding" in result.stdout
    assert "identical measured likelihoods" in result.stderr
