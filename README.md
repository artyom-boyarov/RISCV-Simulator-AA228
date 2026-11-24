# RISC-V Simulator

A Simple RISC-V CPU Simulator with 5 Stage Pipeline, Branch Prediction and Cache Simulation

It is a simple RISC-V Emulator suppprting user mode RV64I instruction set, from PKU Computer Architecture Labs, Spring 2019. I made my project open source in the hope that others can learn from my code about how to make a CPU Emulator and get a deeper understanding in computer architecture. As it is implemented entirely from scratch (with no code from Prof or TA), I think it's fine to make it open source.

Note that this is just a toy for learning and is NOT a robust and full solution to RISC-V CPU Emulation. Use `qemu` for that purpose instead.

## Features

1. Supporting 54 RISC-V instructions from the RV64I instruction set.
2. Branch perdiction module with a set of branch perdicton algorithms.
3. Simulation of five stage pipeline like that in the "Computer Organization and Design, Hardware/Software Interface" Book.
4. Simulation of cache and various cache eviction strategies.

## Compile

```
mkdir build
cd build
cmake ..
make
```

## Usage

```
./Simulator riscv-elf-file-name [-v] [-s] [-d] [-q] [-b strategy] [-f faults.txt] [--no-cache]
```
Parameters:

1. `-v` for verbose output, can redirect output to file for further analysis
2. `-s` for single step execution, often used in combination with `-v`.
3. `-d` for creating memory and register history dump in `dump.txt`
4. `-q` to suppress statistics while retaining the program return value.
5. `-b` for branch prediction strategy (default `NT`), accepted parameters are `AT`, `NT`, `BTFNT` and `BPB`.
   * AT: Randomly predict taken with 70% probability (not taken with 30% probability).
   * NT: Always Not Taken
   * BTFNT: Back Taken Forward Not Taken
   * BPB: Branch Prediction Buffer (2 bit history information)
6. `-f` loads fault configuration from a text file.
7. `--no-cache` bypasses all cache levels for instruction and data accesses.
   L1 cache faults have no effect in this mode.

Guest programs are organized under `kernels/`: smoke tests in `smoke/test` and
`smoke/inclass`, fault-detection kernels in `fault-detection`, reference ELFs
in `bin`, and disassemblies in `assembly`. Simulator unit tests remain in
`test/`.

### Compile a C program for the simulator

With `riscv64-unknown-elf-gcc` installed, run from the repository root:

```sh
./compile-riscv.sh kernels/smoke/inclass/add_regs.c
./build/Simulator kernels/bin/add_regs.riscv
```

The output argument is optional; by default the script writes a `.riscv` file
under `kernels/bin/`. Set `RISCV_GCC` to use a compiler at a different path.
The script links `kernels/start.S`, which calls `main` and exits using the
simulator's `ecall` interface. It builds a freestanding RV64I executable without
libc; programs requiring library functions must provide their own compatible
implementations. Fault-detection and stress kernels use `-O1`; other sources
use GCC's default optimization level.

### Sobel image stress kernel

`kernels/stress/sobel_image.c` adapts the integer Sobel gradient from
[Grayskull](https://github.com/zserge/grayskull/blob/main/grayskull.h) to a
generated 16×16 grayscale image, without file I/O or a C runtime. It leaves the
image border at zero and returns the low 12 bits of a fingerprint of the edge
pixels, in the range 0–4095. The fault-free result is `1690`, verified against
an independent reference. It is a workload result, not a pass/fail return code.

```sh
./compile-riscv.sh kernels/stress/sobel_image.c
./build/Simulator kernels/bin/sobel_image.riscv -q
./build/Simulator kernels/bin/sobel_image.riscv -q -f faults/memory-bit11-stuck-at-0.txt
```

The buffers are placed starting at address `0x000`. Cache and memory faults may
change the fingerprint, be masked, or prevent completion; `--no-cache` can be
used to focus on the memory controller.

### Estimate likelihoods

`generate_likelihoods.py` estimates the tensor used by `VOI_Belief.py`. It
requires NumPy and built simulator
and kernel binaries. By default it selects the seven fault-detection kernels,
the Sobel workload, every `faults/**/*.txt` file, and a no-fault state. It runs
each test 10 times for each state. On an allocated compute node, a batch can
be started directly in a new directory with the desired number of processes:

```sh
python3 generate_likelihoods.py batch likelihood-campaign --processes 16
```

The preparation step writes `manifest.json`, `tests.csv`, and `states.csv`, and
copies the fault configurations into `configs/`. The state index is stable:
for example, the valid-bit stuck-0, stuck-1, and flip faults at 100% are states
0–2, followed by their 50% versions at 3–5. The no-fault state is last.
Properties in the CSV come from file contents rather than filenames.

`batch` prepares the campaign, runs it with Python multiprocessing, then
aggregates the results. Each worker handles one state and exits
(`maxtasksperchild=1`, `chunksize=1`), releasing its process memory before the
next state. Each individual simulator run is also a fresh process. A worker
writes `states/NNNN.npz` after finishing its state and prints a summary after
each set of runs. Rerun the same `batch` command to resume an interrupted
campaign; its existing manifest settings apply. Do not run two batches on the
same directory concurrently. The pool uses Linux's `fork` start method.

For FarmShare Slurm, submit the included script from the repository root:

```sh
sbatch run_likelihoods.sbatch
```

It requests one node, eight CPUs, 8 GiB of memory, and two hours on `normal`.
The worker count follows `SLURM_CPUS_PER_TASK`; for example, override it with
`sbatch --cpus-per-task=16 --mem=16G run_likelihoods.sbatch`. Additional batch
options can be passed after a campaign directory, such as
`sbatch run_likelihoods.sbatch my-campaign --timeout 20`. The script activates
the project's `.venv` and uses its Python, which must have NumPy installed and
be available on the compute node. Build the simulator and kernels on FarmShare
before submitting. FarmShare
[documents Python modules and virtual environments](https://docs.farmshare.stanford.edu/docs/software/);
for example, use `uv venv .venv`, `source .venv/bin/activate`, and
`uv pip install numpy` if NumPy is not available in your chosen environment.

`sbatch` prints a job ID. Check it with `squeue -j JOBID` and follow progress
from the submission directory with `tail -f likelihood-JOBID.out`. Results
are in `likelihood-campaign/` by default. After a time limit, resubmit with the
same campaign directory to resume completed state files. Do not submit two jobs
against the same campaign at once. FarmShare limits and available node sizes can
change; inspect `scontrol show partition normal`, `sinfo -N -p normal -o "%N %c %m %t"`,
and `sacctmgr show qos format=Name,MaxTRESPU,MaxWall` on the cluster before
requesting more CPUs. See FarmShare's [Slurm documentation](https://docs.farmshare.stanford.edu/docs/slurm/)
for partition and quality-of-service details.

The `prepare`, `run`, `run-state`, and `aggregate` subcommands remain available
if you need to execute or inspect the stages separately.

Aggregation requires every state file and writes `likelihoods.npz` and
`outcomes.csv`. Load the tensor and its axis mappings with:

```python
import numpy as np
data = np.load("likelihood-campaign/likelihoods.npz")
L = data["L"]                         # tests × states × outcomes
tests = data["test_names"]            # index -> test
states = data["state_names"]          # index -> fault file, or no_fault
outcomes = data["outcome_labels"]     # index -> observed outcome
```

Each `L[t,s,o]` is the matching count divided by the number of runs; no
smoothing is applied. Labels include `return:<integer>`, `timeout`, nonzero
host `exit:<status>`, and `missing_or_ambiguous_return`. Failures and timeouts
count as observations rather than being silently dropped. Only outcomes observed
in the campaign are included. The file also contains `counts`, `state_properties`,
per-run `seconds`, `mean_seconds`, and `runs`. The kernel's printed return value,
not the host exit status, is used for successful guest exits.

`batch --runs N`, `--timeout SECONDS`, `--branch-strategy NT`, repeatable
`--kernel PATH` and `--fault PATH`, and repeatable `--uncached-test TEST_NAME`
configure a campaign. Cache is enabled by default for every test. Use the same
cache mode for all states of a test; an uncached test cannot observe cache
faults. Inputs are identified by SHA-256 and copied fault files are checked
before each job. Prepare and run on the cluster after building the simulator
there, or transfer the same binaries with the campaign and repository. The
branch predictor affects prediction statistics and timing, so architectural
return values alone may not distinguish branch faults.

### Fault configuration files

Ready-to-use branch predictor and memory examples are in `faults/`.
Use `-f` to enable faults during execution:

```sh
./build/Simulator kernels/bin/add_regs.riscv -f faults.txt
```

Each fault block begins with `type = ...`, followed by `key = value` lines.
Blank lines and `#` comments are ignored. A file can contain one memory fault,
one branch fault, and one L1 cache fault at a time; repeat `type` to start
another block. Later blocks for the same component replace earlier ones. For example:

```text
type = memory
fault = STUCK_AT_0
bit = 3

type = cache
field = tag
fault = BIT_FLIP
bit = 0

type = branch
rate = 0.5
```

Memory accepts `fault` values `STUCK_AT_0`, `STUCK_AT_1`, or `BIT_FLIP` and a
page-offset `bit` from 0–11. Cache faults apply only to L1 and accept those
fault values, a `field` of `valid`, `modified`, `tag`, or `id`, and a
`bit` (0 for valid or modified, 0–31 for tag or id). Branch faults use a
`rate` of `0.5` or `1.0`. The rate is the probability that the configured fault
applies on each eligible access or prediction. For memory and cache faults,
`rate` is optional: it defaults to `0.5` for `BIT_FLIP` and `1.0` for stuck
faults. Branch faults require a rate.
For C++ callers, `Fault::rate` defaults to `1.0` for every fault type; set it
explicitly to `0.5` when a 50% bit-flip rate is desired.
The cache level is always L1; a `level` property is ignored. Configuration
other values are not validated: use the ranges above, since invalid values can cause
undefined behavior. Unknown properties are ignored
and the last value of a repeated property is used. The parser still requires
recognizable fault names and required properties. With no `-f`, faults remain
disabled. Configured faults are enabled after ELF loading
and stack initialization; preexisting cache contents are retained.

### Memory test kernel

`kernels/fault-detection/memory_kernel.c` writes 256 incrementing bytes at `0x000`–`0x0ff`,
then reads and compares that region 16 times. `memory_page_kernel.c` writes all
16 consecutive 256-byte regions before reading and comparing them, covering
the full page at `0x000`–`0xfff`. Values wrap modulo 256, so address `0x001`
contains 1. Both return `0` on success or the first failing address plus one.
For example, a mismatch at `0x001` returns `2`.

`kernels/fault-detection/memory_stride_kernel.c` tests the upper page-offset bits by
writing byte `i` at `0x000 + 16*i` for `i` from 0 to 255, then checking the
same addresses. It covers `0x000`, `0x010`, ..., `0xff0` using the same
return codes; it does not check the bytes between those addresses.

`kernels/fault-detection/memory_address_bits_kernel.c` checks each of the 12
page-offset bits in turn. It first compares pairs whose offsets are all ones
and all ones except that bit, then repeats with all zeros and only that bit
set. Each pair is written with `0xfe` and `0xef` before being read back. It
uses the same return codes and stops at the first mismatch.

`kernels/fault-detection/cache_single_address_kernel.c` tests each byte from
`0x000` through `0xfff`: it writes values 0–15 to that address, then reads
once and checks the final value is 15. Run it with cache enabled to exercise L1;
a mismatch returns the failing address plus one.

`kernels/fault-detection/cache_modified_kernel.c` tests an L1 modified bit
stuck at zero. It writes `0xa5` at `0x000`, reads eight other cache lines
mapping to the same set, then checks `0x000` after eviction. With the current
1 KiB, 64-byte-line, 8-way L1 and cache enabled, an undetected dirty line loses
its writeback and the kernel returns `1`. It returns `0` without the fault.
This kernel is specific to that L1 geometry and does not establish detection of
a modified bit stuck at one.

`kernels/fault-detection/cache_tag_bits_kernel.c` diagnoses a single L1 tag
bit stuck at 0 or 1 at 100% rate. It probes pairs of addresses whose tags
differ in one bit. A zero-tag write/read selects either an all-zero-tag or an
all-one-tag reference, so both stuck directions can be distinguished by bit.
It returns `0` if no mismatch is found, or the first failing tag bit plus one:
bit 0 returns 1, bit 1 returns 2, and so on. Unlike the memory kernels, the
nonzero result encodes a tag bit number, not an address.
This diagnostic assumes the current 1 KiB, 8-way L1 and one deterministic tag
fault; it does not reliably identify 50% faults or other types of faults.
Build it using `compile-riscv.sh`, which supplies the accompanying sparse ELF
sections needed to map probe addresses across the 32-bit address space.

Build and run it with a RISC-V cross-compiler:

```sh
./compile-riscv.sh kernels/fault-detection/memory_page_kernel.c
./build/Simulator kernels/bin/memory_page_kernel.riscv -q --no-cache
./build/Simulator kernels/bin/memory_page_kernel.riscv -q --no-cache -f faults.txt
```

To build the stride kernel, substitute `kernels/fault-detection/memory_stride_kernel.c`
for the page kernel source.

The section placement maps the target region into the ELF; `--no-relax` avoids
relying on a global pointer that the minimal startup does not initialize. The
`--no-cache` makes reads and writes reach the memory controller. This pattern
repeats every 256 bytes, so offset faults in bits 8–11 can alias locations with
identical expected values and go undetected even without cache. Memory faults
are suppressed during instruction fetches but still affect data and stack
accesses, which can prevent the kernel from completing.

### Memory controller faults

In C++, configure a `MemoryFault` and pass it to `MemoryManager::enableFaults`:

```cpp
MemoryFault fault{};
fault.location = FaultLocation::MEMORY_CONTROLLER;
fault.bitPosition = 3; // page-offset bit, from 0 through 11
fault.type = FaultType::STUCK_AT_0; // or STUCK_AT_1 or BIT_FLIP
fault.rate = 1.0; // or 0.5
memory.enableFaults(fault);
// Run the simulation with faults enabled.
memory.disableFaults();
```

The stuck types force the selected offset bit and `BIT_FLIP` flips it, each
with the configured probability per backing-memory byte access.
Faults start disabled. Set them up after loading the program and initializing
memory if those steps should be fault-free. Cache hits bypass the memory
controller; data cache fills and writebacks use it. During an instruction fetch,
memory and cache faults are temporarily disabled, including for any cache
activity caused by that fetch. Enabling or disabling a fault
does not clear caches or undo data already written through a faulty offset.

### Cache metadata faults

Configure a fault on a particular `Cache` instance:

```cpp
CacheFault fault{};
fault.location = FaultLocation::CACHE;
fault.field = CacheFaultField::TAG; // VALID, MODIFIED, TAG, or ID
fault.bitPosition = 0;
fault.type = FaultType::STUCK_AT_1; // or STUCK_AT_0 or BIT_FLIP
fault.rate = 1.0; // or 0.5
cache.enableFaults(fault);
// Run the simulation.
cache.disableFaults();
```

The fault affects metadata reads for all blocks of that cache, including
lookup, replacement, and writeback address calculation. It does not modify
data bits or the stored metadata itself. The stuck types force the selected
bit; `BIT_FLIP` flips it, with the configured probability per metadata read.
Valid and modified accept only bit 0; tag and ID accept bits 0–31.
The `isWrite` and `isHit` fields are not used
by this model. Faults start disabled; disabling one does not undo prior cache
or memory changes.

### Branch predictor faults

Configure a `Fault` with a rate of `0.5` or `1.0`:

```cpp
Fault fault{};
fault.location = FaultLocation::BRANCH_PREDICTOR;
fault.rate = 0.5;
predictor.enableFaults(fault);
// Run the simulation.
predictor.disableFaults();
```

Each prediction is independently inverted with the configured probability,
for any predictor strategy. Faults start disabled; disabling them restores the
strategy's normal behavior. Predictor state updates continue as usual.

When `main` returns, the startup code passes its result in `a0` to exit
system call 93. The simulator prints `Program return value:` followed by the
signed 32-bit C `int` on the next line.
For example, use `return d;` in `add_regs.c` to report its computed result.
The simulator's host exit status remains 0 on a normal guest exit; use the
printed value to capture the full result. A fault can also prevent the program
from reaching the exit call, in which case there is no return-value line.

## Documentation (In Chinese)

See the `doc/` folder.

Also, you can see the corresponding [blog](https://hehao98.github.io/posts/2019/03/riscv-simulator/).



