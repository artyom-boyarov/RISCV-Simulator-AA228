#!/usr/bin/env bash
#SBATCH --job-name=riscv-memory-likelihoods
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=memory-likelihood-%j.out

set -euo pipefail

cd "${SLURM_SUBMIT_DIR:?Submit this job with sbatch from the repository root}"
campaign=${1:-memory-likelihood-campaign}
if (( $# )); then shift; fi

# Keep this campaign limited to the memory configurations selected below.
for arg in "$@"; do
    if [[ "$arg" == --fault || "$arg" == --fault=* ]]; then
        echo "Memory fault files are selected automatically; do not pass --fault" >&2
        exit 1
    fi
done

# A resumed batch uses its existing manifest, regardless of command-line options.
if [[ -f "$campaign/manifest.json" ]]; then
    python3 - "$campaign/manifest.json" <<'PY'
import json
import sys

with open(sys.argv[1]) as f:
    states = json.load(f)["states"]
if any(block.get("type") != "memory" for state in states for block in state["properties"]):
    sys.exit("Cannot resume: campaign contains non-memory faults")
PY
fi

shopt -s nullglob
fault_files=(faults/memory/*.txt)
if (( ${#fault_files[@]} == 0 )); then
    echo "No memory fault files found in faults/memory" >&2
    exit 1
fi
fault_args=()
for file in "${fault_files[@]}"; do
    fault_args+=(--fault "$file")
done

# Reuse the existing environment setup and multiprocessing batch runner.
exec bash run_likelihoods.sbatch "$campaign" "$@" "${fault_args[@]}"
