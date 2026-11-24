#!/usr/bin/env bash
#SBATCH --job-name=riscv-likelihoods
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=likelihood-%j.out

set -euo pipefail

# Submit from the repository root; Slurm writes the log in that directory.
cd "${SLURM_SUBMIT_DIR:?Submit this job with sbatch from the repository root}"
if [[ ! -f generate_likelihoods.py || ! -x build/Simulator ]]; then
    echo "Expected generate_likelihoods.py and executable build/Simulator in $PWD" >&2
    exit 1
fi

if [[ ! -f .venv/bin/activate ]]; then
    echo "Expected project virtual environment at $PWD/.venv" >&2
    exit 1
fi
# shellcheck source=/dev/null
source .venv/bin/activate
python_bin="$VIRTUAL_ENV/bin/python"

# The Python worker pool supplies parallelism; avoid hidden numerical-library
# threads multiplying the number of runnable processes.
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
if ! "$python_bin" -c 'import numpy'; then
    echo "NumPy is unavailable in $VIRTUAL_ENV; install it in the project virtual environment" >&2
    exit 1
fi

campaign=${1:-likelihood-campaign}
if (( $# )); then shift; fi
workers=${SLURM_CPUS_PER_TASK:?Slurm did not provide SLURM_CPUS_PER_TASK}
echo "Job ${SLURM_JOB_ID:-unknown} on ${HOSTNAME:-unknown}: $workers workers, campaign $campaign"
echo "Starting $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# The final --processes argument keeps worker count tied to the Slurm allocation.
exec "$python_bin" -u generate_likelihoods.py batch "$campaign" "$@" --processes "$workers"
