#!/usr/bin/env python3
"""Run random kernels against a selected fault and update the state belief."""

import argparse
from pathlib import Path
import random
import sys
import tempfile

import numpy as np

from generate_likelihoods import load_manifest, require_supported_state, resolve_path, run_one
from VOI_Belief import update_belief


def select_state(value, names, rng):
    if value is None:
        candidates = [index for index, name in enumerate(names) if name != "no_fault"]
        if not candidates:
            raise ValueError("No fault states available to choose randomly")
        return rng.choice(candidates)
    try:
        index = int(value)
    except ValueError:
        if value not in names:
            raise ValueError(f"Unknown state {value!r}; see states.csv")
        return names.index(value)
    if not 0 <= index < len(names):
        raise ValueError(f"State index must be between 0 and {len(names) - 1}")
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", nargs="?", default="likelihood-campaign")
    parser.add_argument("--state", help="state index or exact state name; default: random fault")
    parser.add_argument("--seed", type=int, help="seed for choosing the state and tests")
    parser.add_argument("--threshold", type=float, default=0.9)
    parser.add_argument("--max-steps", type=int, help="stop without convergence after this many tests")
    parser.add_argument("--simulator", default="build/Simulator")
    args = parser.parse_args()
    if not 0 < args.threshold < 1:
        parser.error("--threshold must be between 0 and 1")
    if args.max_steps is not None and args.max_steps < 1:
        parser.error("--max-steps must be positive")

    campaign = Path(args.campaign).resolve()
    manifest = load_manifest(campaign)
    with np.load(campaign / "likelihoods.npz", allow_pickle=False) as data:
        L = data["L"]
        tests = data["test_names"].tolist()
        states = data["state_names"].tolist()
        outcomes = data["outcome_labels"].tolist()
    if tests != [item["name"] for item in manifest["tests"]] or states != [item["name"] for item in manifest["states"]]:
        raise ValueError("Likelihood axes do not match the campaign manifest")
    if L.shape != (len(tests), len(states), len(outcomes)) or not len(tests) or not len(states):
        raise ValueError("Invalid likelihood tensor dimensions")
    if len(outcomes) != len(set(outcomes)) or not np.all(np.isfinite(L)) or np.any(L < 0) or not np.allclose(L.sum(axis=2), 1):
        raise ValueError("Invalid likelihood probabilities or duplicate outcome labels")

    simulator = resolve_path(args.simulator).resolve()
    rng = random.Random(args.seed)
    chosen = select_state(args.state, states, rng)
    state = manifest["states"][chosen]
    require_supported_state(state)
    config = campaign / state["config"] if state["config"] else None
    outcome_index = {label: index for index, label in enumerate(outcomes)}
    belief = np.full(len(states), 1.0 / len(states))
    print(f"True state: {chosen}: {states[chosen]}", flush=True)
    print(f"Uniform prior over {len(states)} states; random-test seed: {args.seed}; "
          f"stop threshold: > {args.threshold:.3f}", flush=True)
    equivalent = np.flatnonzero(np.all(L == L[:, chosen:chosen + 1, :], axis=(0, 2)))
    if len(equivalent) > 1:
        print(f"Warning: the true state shares identical measured likelihoods with "
              f"{len(equivalent) - 1} other states. With this uniform prior they remain "
              f"tied, limiting each to at most {1.0 / len(equivalent):.6f} belief; "
              "another state may still be selected incorrectly. "
              "Use --max-steps to bound the experiment.", file=sys.stderr, flush=True)

    step = 0
    with tempfile.TemporaryDirectory(prefix="belief-experiment-") as scratch:
        while args.max_steps is None or step < args.max_steps:
            t = rng.randrange(len(tests))
            test = manifest["tests"][t]
            label, seconds = run_one(str(simulator), str(resolve_path(test["path"])), config,
                                     test["no_cache"], manifest["branch_strategy"],
                                     manifest["timeout_seconds"], scratch)
            step += 1
            print(f"\nTest {step}: {tests[t]} -> {label} ({seconds:.3f} s)", flush=True)
            if label not in outcome_index:
                print(f"Cannot update: outcome {label!r} was not observed in the likelihood campaign.",
                      file=sys.stderr, flush=True)
                return 2
            o = outcome_index[label]
            evidence = float(belief @ L[t, :, o])
            if evidence <= 0:
                print("Cannot update: this outcome has zero likelihood under every state "
                      "with nonzero current belief.", file=sys.stderr, flush=True)
                return 2
            if L[t, chosen, o] == 0 and belief[chosen] > 0:
                print("Warning: this outcome had zero measured likelihood for the true state; "
                      "the update will eliminate it.", file=sys.stderr, flush=True)
            belief = update_belief(belief, L, t, o)
            top = np.argsort(-belief, kind="stable")[:min(5, len(states))]
            for rank, s in enumerate(top, 1):
                print(f"  {rank}. state {s}: {states[s]}  P={belief[s]:.6f}", flush=True)
            best = int(top[0])
            if belief[best] > args.threshold:
                print(f"\nStopped after {step} tests: state {best} has probability {belief[best]:.6f}; "
                      f"{'correct' if best == chosen else 'incorrect'} diagnosis.", flush=True)
                return 0
    print(f"Stopped after {step} tests without exceeding the threshold.", flush=True)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(2)
