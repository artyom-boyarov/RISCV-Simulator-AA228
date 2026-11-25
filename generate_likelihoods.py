#!/usr/bin/env python3
"""Run fault campaigns locally or as independent HPC jobs, then build L[t,s,o]."""

import argparse
import csv
import json
import multiprocessing
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

try:
    import numpy as np
except ImportError:
    sys.exit("NumPy is required; on Ubuntu install python3-numpy.")

ROOT = Path(__file__).resolve().parent
RETURN = re.compile(rb"^Program return value:\s*\n\s*(-?\d+)\s*$", re.MULTILINE)
FIELD_ORDER = {"valid": 0, "modified": 1, "tag": 2, "id": 3}
TYPE_ORDER = {"STUCK_AT_0": 0, "STUCK_AT_1": 1, "BIT_FLIP": 2}


def fault_properties(text):
    """Describe all blocks as the simulator sees them, including default rates."""
    blocks = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"Invalid fault line: {raw!r}")
        key, value = (part.strip() for part in line.split("=", 1))
        if key == "type":
            blocks.append({"type": value})
        elif not blocks:
            raise ValueError("Fault file must begin with type")
        else:
            blocks[-1][key] = value
    if not blocks:
        raise ValueError("Empty fault file")
    for block in blocks:
        kind = block["type"]
        if kind in ("cache", "memory"):
            if "fault" not in block or "bit" not in block or (kind == "cache" and "field" not in block):
                raise ValueError("Fault file is missing required properties")
            block["rate"] = float(block.get("rate", 0.5 if block["fault"] == "BIT_FLIP" else 1.0))
            block["bit"] = int(block["bit"])
        elif kind == "branch_resolution":
            if "fault" not in block:
                raise ValueError("Branch resolution fault is missing fault property")
            block["rate"] = float(block["rate"])
        else:
            raise ValueError(f"Unknown fault type: {kind}")
        if block["rate"] not in (0.5, 1.0):
            raise ValueError("Fault rate must be 0.5 or 1.0")
    return blocks


def fault_sort_key(state):
    blocks = state["properties"]
    if len(blocks) != 1:
        return (3, state["name"])
    p = blocks[0]
    if p["type"] == "cache":
        return (0, FIELD_ORDER.get(p["field"], 99), p["bit"], -p["rate"],
                TYPE_ORDER.get(p["fault"], 99), state["name"])
    if p["type"] == "memory":
        return (1, p["bit"], -p["rate"], TYPE_ORDER.get(p["fault"], 99), state["name"])
    return (2, -p["rate"], state["name"])


def resolve_path(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def portable_path(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_csv(path, rows, fields):
    with path.open("w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prepare(args):
    campaign = Path(args.campaign).resolve()
    if campaign.exists() and any(campaign.iterdir()):
        raise ValueError(f"Campaign directory is not empty: {campaign}")
    if args.runs < 1 or args.branch_runs < 1 or args.timeout <= 0:
        raise ValueError("runs, branch-runs, and timeout must be positive")
    simulator = resolve_path(args.simulator).resolve()
    if not simulator.is_file() or not os.access(simulator, os.X_OK):
        raise ValueError(f"Simulator executable not found: {simulator}")
    fault_paths = [Path(p).resolve() for p in args.fault] if args.fault else sorted((ROOT / "faults").rglob("*.txt"))
    if not fault_paths:
        raise ValueError("No fault files found")
    sources = sorted((ROOT / "kernels/fault-detection").glob("*.c")) + sorted((ROOT / "kernels/stress").glob("*.c"))
    kernel_paths = [Path(p).resolve() for p in args.kernel] if args.kernel else [ROOT / "kernels/bin" / (p.stem + ".riscv") for p in sources]
    tests = []
    for path in kernel_paths:
        path = path.resolve()
        if not path.is_file():
            raise ValueError(f"Kernel executable missing: {path}; compile the kernel first")
        if any(t["name"] == path.stem for t in tests):
            raise ValueError(f"Duplicate kernel name: {path.stem}")
        tests.append({"index": len(tests), "name": path.stem, "path": portable_path(path),
                      "no_cache": path.stem in args.uncached_test})
    unknown = set(args.uncached_test) - {t["name"] for t in tests}
    if unknown:
        raise ValueError(f"Unknown uncached tests: {', '.join(sorted(unknown))}")
    states = []
    for path in fault_paths:
        content = path.read_text()
        try:
            name = str(path.relative_to(ROOT))
        except ValueError:
            name = str(path)
        states.append({"name": name, "properties": fault_properties(content), "content": content})
    states.sort(key=fault_sort_key)
    states.append({"name": "no_fault", "properties": [], "content": None})
    campaign.mkdir(parents=True, exist_ok=True)
    (campaign / "configs").mkdir()
    (campaign / "states").mkdir()
    for i, state in enumerate(states):
        state["index"] = i
        state["runs"] = args.branch_runs if any(p["type"] == "branch_resolution" for p in state["properties"]) else args.runs
        content = state.pop("content")
        state["config"] = None
        if content is not None:
            relative = f"configs/{i:04d}.txt"
            (campaign / relative).write_text(content)
            state["config"] = relative
    manifest = {"version": 1, "simulator": portable_path(simulator),
                "runs": args.runs, "timeout_seconds": args.timeout, "branch_strategy": args.branch_strategy,
                "tests": tests, "states": states}
    (campaign / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_csv(campaign / "tests.csv", tests, ("index", "name", "path", "no_cache"))
    state_rows = [dict(s, properties=json.dumps(s["properties"], sort_keys=True)) for s in states]
    write_csv(campaign / "states.csv", state_rows, ("index", "name", "config", "properties", "runs"))
    print(f"Prepared {len(tests)} tests × {len(states)} states = "
          f"{len(tests) * sum(s['runs'] for s in states)} simulations in {campaign} "
          f"({args.runs} runs normally, {args.branch_runs} for branch resolution faults)", flush=True)


def load_manifest(campaign):
    return json.loads((campaign / "manifest.json").read_text())


def require_supported_state(state):
    if any(block.get("type") == "branch" for block in state.get("properties", [])):
        raise ValueError("This campaign contains a removed branch predictor fault; "
                         "use the original simulator or prepare a new campaign")


def run_one(simulator, kernel, config, no_cache, strategy, timeout, scratch):
    cmd = [simulator, kernel, "-q", "-b", strategy]
    if no_cache:
        cmd.append("--no-cache")
    if config:
        cmd.extend(("-f", str(config)))
    start = time.monotonic()
    # stdout goes to a file, not RAM; discard noisy diagnostics and isolate dump.txt.
    with tempfile.TemporaryFile(dir=scratch) as output:
        try:
            proc = subprocess.run(cmd, cwd=scratch, stdout=output, stderr=subprocess.DEVNULL,
                                  timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return "timeout", time.monotonic() - start
        elapsed = time.monotonic() - start
        if proc.returncode != 0:
            return f"exit:{proc.returncode}", elapsed
        size = output.tell()
        output.seek(max(0, size - 1024 * 1024))
        matches = list(RETURN.finditer(output.read()))
        if len(matches) != 1:
            return "missing_or_ambiguous_return", elapsed
        return f"return:{int(matches[0].group(1))}", elapsed


def run_state(campaign_arg, index):
    campaign = Path(campaign_arg).resolve()
    manifest = load_manifest(campaign)
    if index < 0 or index >= len(manifest["states"]):
        raise ValueError(f"State index must be between 0 and {len(manifest['states']) - 1}")
    state = manifest["states"][index]
    require_supported_state(state)
    runs = state.get("runs", manifest["runs"])
    destination = campaign / "states" / f"{index:04d}.npz"
    if destination.exists():
        raise FileExistsError(f"State result already exists: {destination}")
    simulator = resolve_path(manifest["simulator"])
    config = campaign / state["config"] if state["config"] else None
    outcomes, times = [], []
    with tempfile.TemporaryDirectory(prefix=f"likelihood-{index}-") as scratch:
        for test in manifest["tests"]:
            kernel = resolve_path(test["path"])
            results = [run_one(str(simulator), str(kernel), config, test["no_cache"],
                               manifest["branch_strategy"], manifest["timeout_seconds"], scratch)
                       for _ in range(runs)]
            row, durations = zip(*results)
            outcomes.append(row)
            times.append(durations)
            counts = {label: row.count(label) for label in sorted(set(row))}
            print(f"state {index:04d} {state['name']} | test {test['index']:02d} {test['name']} | "
                  f"{runs} runs: {counts}", flush=True)
    # Atomic finalization prevents an interrupted task from looking complete.
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".npz", delete=False) as temp:
        temporary = Path(temp.name)
        try:
            np.savez_compressed(temp, state_index=index, worker_pid=os.getpid(),
                                outcomes=np.asarray(outcomes), seconds=np.asarray(times))
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, destination)
    return index


def aggregate(args):
    campaign = Path(args.campaign).resolve()
    manifest = load_manifest(campaign)
    states, tests, runs = manifest["states"], manifest["tests"], manifest["runs"]
    runs_per_state = np.asarray([s.get("runs", runs) for s in states], dtype=np.int64)
    missing = [s["index"] for s in states if not (campaign / "states" / f"{s['index']:04d}.npz").is_file()]
    if missing:
        raise ValueError(f"Missing {len(missing)} state results; first indices: {missing[:20]}")
    destination = campaign / "likelihoods.npz"
    if destination.exists():
        raise FileExistsError(f"Aggregate already exists: {destination}")
    state_outcomes, state_seconds = [], []
    for state, state_runs in zip(states, runs_per_state):
        with np.load(campaign / "states" / f"{state['index']:04d}.npz", allow_pickle=False) as data:
            if (int(data["state_index"]) != state["index"] or
                    data["outcomes"].shape != (len(tests), state_runs) or
                    data["seconds"].shape != (len(tests), state_runs)):
                raise ValueError(f"Invalid result for state {state['index']}")
            state_outcomes.append(data["outcomes"].tolist())
            state_seconds.append(data["seconds"])
    labels = {label for rows in state_outcomes for row in rows for label in row}
    labels = sorted(labels, key=lambda s: (0, int(s[7:])) if s.startswith("return:") else (1, s))
    index = {label: i for i, label in enumerate(labels)}
    counts = np.zeros((len(tests), len(states), len(labels)), dtype=np.int64)
    for s, rows in enumerate(state_outcomes):
        for t, row in enumerate(rows):
            for label in row:
                counts[t, s, index[label]] += 1
    seconds = np.full((len(tests), len(states), int(runs_per_state.max())), np.nan)
    for s, values in enumerate(state_seconds):
        seconds[:, s, :runs_per_state[s]] = values
    mean_seconds = np.stack([values.mean(axis=1) for values in state_seconds], axis=1)
    write_csv(campaign / "outcomes.csv", [{"index": i, "label": label} for i, label in enumerate(labels)],
              ("index", "label"))
    # Keep an interrupted aggregation from leaving a partial final result.
    with tempfile.NamedTemporaryFile(dir=campaign, suffix=".npz", delete=False) as temp:
        temporary = Path(temp.name)
        try:
            np.savez_compressed(temp, L=counts / runs_per_state[np.newaxis, :, np.newaxis], counts=counts,
                                outcome_labels=np.asarray(labels), test_names=np.asarray([t["name"] for t in tests]),
                                state_names=np.asarray([s["name"] for s in states]),
                                state_properties=np.asarray([json.dumps(s["properties"], sort_keys=True) for s in states]),
                                seconds=seconds, mean_seconds=mean_seconds, runs=runs,
                                runs_per_state=runs_per_state)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    os.replace(temporary, destination)
    print(f"Saved {destination}: L shape {counts.shape}; observations per state: "
          f"{sorted(set(runs_per_state.tolist()))}", flush=True)


def _run_state_task(task):
    campaign, index = task
    return run_state(campaign, index)


def run_all(args):
    if args.processes < 1:
        raise ValueError("processes must be positive")
    campaign = Path(args.campaign).resolve()
    manifest = load_manifest(campaign)
    indices = [s["index"] for s in manifest["states"]
               if not (campaign / "states" / f"{s['index']:04d}.npz").exists()]
    print(f"Running {len(indices)} remaining states with {args.processes} processes", flush=True)
    if not indices:
        print("All state jobs completed", flush=True)
        return
    # Linux HPC nodes support fork. A single state per child releases all worker
    # memory between states; chunksize=1 makes one state exactly one pool task.
    context = multiprocessing.get_context("fork")
    with context.Pool(processes=args.processes, maxtasksperchild=1) as pool:
        for _ in pool.imap_unordered(_run_state_task,
                                     ((str(campaign), i) for i in indices), chunksize=1):
            pass
    print("All state jobs completed", flush=True)


def batch(args):
    campaign = Path(args.campaign).resolve()
    if (campaign / "manifest.json").exists():
        print(f"Resuming existing campaign {campaign}; its manifest settings apply", flush=True)
    else:
        prepare(args)
    run_all(args)
    aggregate(args)


def add_prepare_arguments(parser):
    parser.add_argument("campaign")
    parser.add_argument("--simulator", default="build/Simulator")
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--branch-runs", type=int, default=100,
                        help="runs per test for states containing a branch resolution fault (default: 100)")
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds per simulation")
    parser.add_argument("--branch-strategy", choices=("AT", "NT", "BTFNT", "BPB"), default="NT")
    parser.add_argument("--kernel", action="append", default=[], help="select kernel binary; repeatable")
    parser.add_argument("--fault", action="append", default=[], help="select fault file; repeatable")
    parser.add_argument("--uncached-test", action="append", default=[], help="kernel name to run with --no-cache")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("prepare", help="Snapshot inputs and enumerate tests and fault states")
    add_prepare_arguments(create)
    create.set_defaults(func=prepare)
    worker = commands.add_parser("run-state", help="Run all tests for a single enumerated state")
    worker.add_argument("campaign")
    worker.add_argument("state", type=int)
    worker.set_defaults(func=lambda a: run_state(a.campaign, a.state))
    local = commands.add_parser("run", help="Run all unfinished state jobs with a local process pool")
    local.add_argument("campaign")
    local.add_argument("--processes", type=int, default=1)
    local.set_defaults(func=run_all)
    full = commands.add_parser("batch", help="Prepare, run with multiprocessing, and aggregate")
    add_prepare_arguments(full)
    full.add_argument("--processes", type=int, default=1)
    full.set_defaults(func=batch)
    combine = commands.add_parser("aggregate", help="Collect state results into likelihoods.npz")
    combine.add_argument("campaign")
    combine.set_defaults(func=aggregate)
    args = parser.parse_args()
    try:
        args.func(args)
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
