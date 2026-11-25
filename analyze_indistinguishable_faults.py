#!/usr/bin/env python3
"""Report states with identical empirical likelihoods across every test."""

import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np


def report(path):
    with np.load(path, allow_pickle=False) as data:
        likelihoods = data["L"]
        names = data["state_names"].tolist()
        tests = data["test_names"].tolist()
        outcomes = data["outcome_labels"].tolist()
        runs = int(data["runs"])
    if likelihoods.ndim != 3 or likelihoods.shape != (len(tests), len(names), len(outcomes)):
        raise ValueError("Likelihood tensor dimensions do not match its labels")
    if not np.isfinite(likelihoods).all():
        raise ValueError("Likelihood tensor contains non-finite values")

    groups = defaultdict(list)
    for state in range(len(names)):
        # Exact equality across the complete test × outcome likelihood matrix.
        groups[likelihoods[:, state, :].tobytes()].append(state)
    duplicates = [indices for indices in groups.values() if len(indices) > 1]
    ambiguous = sum(map(len, duplicates))
    lines = [
        "# States with identical observed likelihoods", "",
        f"Source: `{path}`. {len(tests)} tests, {len(names)} states, "
        f"{len(outcomes)} observed outcome labels, {runs} runs per test and state.", "",
        f"{len(duplicates)} matching groups contain {ambiguous} states; "
        f"the other {len(names) - ambiguous} states have unique observed likelihoods.", "",
        "States in each group have exactly the same empirical likelihood for every "
        "test and outcome, including timeouts and simulator failures when present. "
        "State indices and names refer to this campaign's saved enumeration.", "",
        "These are comparisons of finite samples, not proof that the underlying "
        "probabilities are identical or different. With only this many runs, "
        "rare outcomes can be missed and sampling noise can make matching true "
        "distributions look different. Unique estimates do not guarantee reliable "
        "diagnosis; repeated tests and more samples may change the result.", "",
    ]
    for number, indices in enumerate(duplicates, 1):
        lines += [f"## Group {number}: {len(indices)} states", ""]
        lines += [f"- `{i}`: `{names[i]}`" for i in indices]
        lines += ["", "Shared observed likelihoods:", ""]
        for t, test in enumerate(tests):
            row = likelihoods[t, indices[0], :]
            observed = ", ".join(f"`{outcomes[o]}`: {row[o]:.6g}" for o in np.flatnonzero(row))
            lines.append(f"- `{test}`: {observed}")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("likelihoods", type=Path, help="campaign likelihoods.npz")
    parser.add_argument("--output", type=Path, help="write Markdown report to this file")
    args = parser.parse_args()
    result = report(args.likelihoods)
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
