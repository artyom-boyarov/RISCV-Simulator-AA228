import json
import pathlib
import subprocess
import sys
import tempfile

try:
    import numpy as np
except ImportError:
    sys.exit(77)

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from generate_likelihoods import checksum

with tempfile.TemporaryDirectory() as directory:
    path = pathlib.Path(directory)
    simulator = path / "simulator"
    simulator.write_text("#!/usr/bin/env python3\nprint('Program return value:\\n0')\n")
    simulator.chmod(0o755)
    kernel = path / "kernel.riscv"
    kernel.touch()
    campaign = path / "campaign"
    campaign.mkdir()
    manifest = {"simulator_sha256": checksum(simulator), "branch_strategy": "NT",
                "tests": [{"name": "kernel", "path": str(kernel),
                           "sha256": checksum(kernel), "no_cache": False}]}
    (campaign / "manifest.json").write_text(json.dumps(manifest))
    np.savez(campaign / "likelihoods.npz", test_names=np.asarray(["kernel"]),
             state_names=np.asarray(["no_fault"]), outcome_labels=np.asarray(["return:0"]),
             counts=np.asarray([[[2]]]))

    def run(*extra):
        return subprocess.run([sys.executable, str(root / "measure_kernel_costs.py"),
                               str(campaign), "--simulator", str(simulator), "--runs", "2", *extra],
                              text=True, capture_output=True)

    result = run()
    assert result.returncode == 0, result.stderr
    with np.load(campaign / "test_costs.npz", allow_pickle=False) as data:
        assert data["test_names"].tolist() == ["kernel"]
        assert data["seconds"].shape == (1, 2)
        assert np.all(data["seconds"] > 0)
        np.testing.assert_allclose(data["cost"], data["seconds"].mean(axis=1))
    assert run().returncode != 0  # Existing results are protected by default.
    assert run("--overwrite").returncode == 0

    # A wrong no-fault result must not be silently included in the cost estimate.
    np.savez(campaign / "likelihoods.npz", test_names=np.asarray(["kernel"]),
             state_names=np.asarray(["no_fault"]), outcome_labels=np.asarray(["return:9"]),
             counts=np.asarray([[[2]]]))
    bad_output = campaign / "bad_costs.npz"
    result = run("--output", str(bad_output))
    assert result.returncode != 0 and "unexpected outcome" in result.stderr
    assert not bad_output.exists()
