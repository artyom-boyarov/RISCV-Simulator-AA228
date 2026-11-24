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
implementations. `-O0` keeps calculations available for instruction tracing.

### Fault configuration files

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
rate = 0.3
```

Memory accepts `fault` values `STUCK_AT_0`, `STUCK_AT_1`, or `BIT_FLIP` and a
page-offset `bit` from 0–11. Cache faults apply only to L1 and accept those
fault values, a `field` of `valid`, `modified`, `tag`, or `id`, and a
`bit` (0 for valid or modified, 0–31 for tag or id). Branch faults use a
`rate` from 0–1. Memory and cache `BIT_FLIP` faults use a fixed 50% probability.
The cache level is always L1; a `level` property is ignored. Configuration
values are not validated: use the ranges above, since invalid values can cause
undefined behavior. Unknown properties are ignored
and the last value of a repeated property is used. The parser still requires
recognizable fault names and required properties. With no `-f`, faults remain
disabled. Configured faults are enabled after ELF loading
and stack initialization; preexisting cache contents are retained.

### Memory test kernel

`kernels/fault-detection/memory_kernel.c` writes 256 incrementing bytes at `0x1000`–`0x10ff`,
then reads and compares that region 16 times. `memory_page_kernel.c` writes all
16 consecutive 256-byte regions before reading and comparing them, covering
the full page at `0x1000`–`0x1fff`. Values wrap modulo 256, so address `0x1001`
contains 1. Both return 0 on success, or `(failing_address << 2) | 1` on the
first mismatch. For example, a mismatch at `0x1001` returns `0x4005` (16389).

`kernels/fault-detection/memory_stride_kernel.c` tests the upper page-offset bits by
writing byte `i` at `0x1000 + 16*i` for `i` from 0 to 255, then checking the
same addresses. It covers `0x1000`, `0x1010`, ..., `0x1ff0` using the same
return codes; it does not check the bytes between those addresses.

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
identical expected values and go undetected even without cache. Faults also
affect instruction fetches and can prevent the kernel from completing.

### Memory controller faults

In C++, configure a `MemoryFault` and pass it to `MemoryManager::enableFaults`:

```cpp
MemoryFault fault{};
fault.location = FaultLocation::MEMORY_CONTROLLER;
fault.bitPosition = 3; // page-offset bit, from 0 through 11
fault.type = FaultType::STUCK_AT_0; // or STUCK_AT_1 or BIT_FLIP
memory.enableFaults(fault);
// Run the simulation with faults enabled.
memory.disableFaults();
```

The stuck types force the selected offset bit on each backing-memory access;
`BIT_FLIP` flips it independently with 50% probability per byte access. The
inherited `rate` field is not used for these fixed-probability fault types.
Faults start disabled. Set them up after loading the program and initializing
memory if those steps should be fault-free. Cache hits bypass the memory
controller; cache fills and writebacks use it. Enabling or disabling a fault
does not clear caches or undo data already written through a faulty offset.

### Cache metadata faults

Configure a fault on a particular `Cache` instance:

```cpp
CacheFault fault{};
fault.location = FaultLocation::CACHE;
fault.field = CacheFaultField::TAG; // VALID, MODIFIED, TAG, or ID
fault.bitPosition = 0;
fault.type = FaultType::STUCK_AT_1; // or STUCK_AT_0 or BIT_FLIP
cache.enableFaults(fault);
// Run the simulation.
cache.disableFaults();
```

The fault affects metadata reads for all blocks of that cache, including
lookup, replacement, and writeback address calculation. It does not modify
data bits or the stored metadata itself. The stuck types force the selected
bit; `BIT_FLIP` flips it with 50% probability independently on each metadata
read. Valid and modified accept only bit 0; tag and ID accept bits 0–31.
The inherited `rate` and the `addr`, `isWrite`, and `isHit` fields are not used
by this model. Faults start disabled; disabling one does not undo prior cache
or memory changes.

### Branch predictor faults

Configure a `Fault` with a probability between 0 and 1:

```cpp
Fault fault{};
fault.location = FaultLocation::BRANCH_PREDICTOR;
fault.rate = 0.3;
predictor.enableFaults(fault);
// Run the simulation.
predictor.disableFaults();
```

Each prediction is independently inverted with the configured probability,
for any predictor strategy. Faults start disabled; disabling them restores the
strategy's normal behavior. Predictor state updates continue as usual. Invalid
locations and probabilities are not validated.

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



