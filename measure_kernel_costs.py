#!/usr/bin/env python3
"""Measure serial, fault-free wall time for the tests in a likelihood campaign."""

import argparse
import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

import numpy as np

from generate_likelihoods import RETURN, load_manifest, resolve_path


def measure_one(simulator, kernel, no_cache, strategy, timeout, scratch):
    cmd = [simulator, kernel, "-q", "-b", strategy]
    if no_cache:
        cmd.append("--no-cache")
    start = time.monotonic()
    try:
        # A pipe allows communicate() to wake promptly on EOF instead of
        # polling waitpid at intervals when a timeout is configured.
        result = subprocess.run(cmd, cwd=scratch, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", time.monotonic() - start
    elapsed = time.monotonic() - start
    if result.returncode != 0:
        return f"exit:{result.returncode}", elapsed
    matches = list(RETURN.finditer(result.stdout))
    if len(matches) != 1:
        return "missing_or_ambiguous_return", elapsed
    return f"return:{int(matches[0].group(1))}", elapsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", help="directory containing manifest.json and likelihoods.npz")
    parser.add_argument("--runs", type=int, default=10, help="fault-free runs per test (default: 10)")
    parser.add_argument("--timeout", type=float, default=30, help="timeout per run in seconds")
    parser.add_argument("--simulator", default="build/Simulator", help="simulator executable to time")
    parser.add_argument("--output", help="output .npz path (default: CAMPAIGN/test_costs.npz)")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")
    args = parser.parse_args()
    if args.runs < 1 or args.timeout <= 0:
        parser.error("--runs and --timeout must be positive")

    campaign = Path(args.campaign).resolve()
    manifest = load_manifest(campaign)
    output = Path(args.output).resolve() if args.output else campaign / "test_costs.npz"
    csv_path = output.with_suffix(".csv")
    if output.suffix != ".npz":
        parser.error("--output must end in .npz")
    if not args.overwrite and (output.exists() or csv_path.exists()):
        raise FileExistsError(f"Refusing to overwrite {output} or {csv_path}")
    if not output.parent.is_dir():
        raise FileNotFoundError(f"Output directory does not exist: {output.parent}")

    simulator = resolve_path(args.simulator).resolve()
    if not simulator.is_file() or not os.access(simulator, os.X_OK):
        raise ValueError(f"Simulator executable not found: {simulator}")
    tests = manifest["tests"]
    with np.load(campaign / "likelihoods.npz", allow_pickle=False) as data:
        if data["test_names"].tolist() != [t["name"] for t in tests]:
            raise ValueError("Likelihood test order does not match the campaign manifest")
        states = data["state_names"].tolist()
        if states.count("no_fault") != 1:
            raise ValueError("Expected exactly one no_fault state")
        baseline = states.index("no_fault")
        labels = data["outcome_labels"].tolist()
        allowed = [{labels[o] for o in np.flatnonzero(data["counts"][t, baseline])}
                   for t in range(len(tests))]
    if any(not values or any(not s.startswith("return:") for s in values) for values in allowed):
        raise ValueError("Campaign no-fault baseline contains a missing return, timeout, or crash")

    samples = []
    with tempfile.TemporaryDirectory(prefix="kernel-costs-") as scratch:
        for t, test in enumerate(tests):
            binary = resolve_path(test["path"])
            times = []
            for run in range(args.runs):
                label, seconds = measure_one(str(simulator), str(binary), test["no_cache"],
                                             manifest["branch_strategy"], args.timeout, scratch)
                if label not in allowed[t]:
                    raise RuntimeError(f"{test['name']} run {run + 1}: unexpected outcome {label}; "
                                       f"campaign no-fault outcomes: {sorted(allowed[t])}")
                times.append(seconds)
            samples.append(times)
            print(f"{t:02d} {test['name']}: mean {np.mean(times):.6f} s, "
                  f"median {np.median(times):.6f} s ({args.runs} runs)", flush=True)

    seconds = np.asarray(samples, dtype=np.float64)
    cost = seconds.mean(axis=1)
    names = np.asarray([test["name"] for test in tests])
    np.savez_compressed(output, cost=cost, seconds=seconds, test_names=names,
                        median_seconds=np.median(seconds, axis=1),
                        std_seconds=seconds.std(axis=1), simulator=str(simulator),
                        branch_strategy=manifest["branch_strategy"],
                        no_cache=np.asarray([test["no_cache"] for test in tests]),
                        host=platform.node(), platform=platform.platform(),
                        measured_at_utc=datetime.now(timezone.utc).isoformat())
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(("index", "test", "mean_seconds", "median_seconds", "std_seconds", "runs", "no_cache"))
        for i, test in enumerate(tests):
            writer.writerow((i, test["name"], cost[i], np.median(seconds[i]),
                             seconds[i].std(), args.runs, test["no_cache"]))
    print(f"Saved {output} and {csv_path}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
