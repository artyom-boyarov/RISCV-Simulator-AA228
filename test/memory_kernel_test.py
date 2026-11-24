import pathlib
import re
import subprocess
import sys
import tempfile

compiler, simulator, source, page_source, stride_source, startup = sys.argv[1:]

with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    def compile_kernel(source, name):
        elf = root / name
        subprocess.run([compiler, "-march=rv64i", "-mabi=lp64", "-O1",
                        "-ffreestanding", "-nostdlib", "-static", "-Wl,-e,_start",
                        "-Wl,--no-relax", "-Wl,--section-start=.memory_region=0x1000",
                        startup, source, "-o", str(elf)], check=True)
        return elf

    elf = compile_kernel(source, "memory_kernel.riscv")
    page_elf = compile_kernel(page_source, "memory_page_kernel.riscv")
    stride_elf = compile_kernel(stride_source, "memory_stride_kernel.riscv")

    def run(config=None, binary=elf, no_cache=False):
        args = [simulator, str(binary), "-q"]
        if no_cache:
            args += ["--no-cache"]
        if config is not None:
            path = root / "fault.txt"
            path.write_text(config)
            args += ["-f", str(path)]
        result = subprocess.run(args, cwd=directory, text=True, capture_output=True,
                                timeout=45)
        assert result.returncode == 0, result.stderr[-2000:]
        match = re.search(r"Program return value:\s*(-?\d+)", result.stdout)
        assert match, result.stdout
        return int(match.group(1))

    assert run() == 0
    assert run("type = memory\nfault = STUCK_AT_0\nbit = 11\n") == 0
    assert run("type = cache\nfield = modified\nfault = STUCK_AT_0\nbit = 0\n") == 0
    assert run("type = cache\nfield = tag\nfault = STUCK_AT_0\nbit = 0\n") == ((0x1001 << 2) | 1)
    assert run(binary=page_elf) == 0
    assert run(binary=page_elf, no_cache=True) == 0
    # High-offset aliasing is invisible to a byte pattern that repeats every 256 bytes.
    assert run("type = memory\nfault = STUCK_AT_0\nbit = 11\n", page_elf, True) == 0
    assert run(binary=stride_elf, no_cache=True) == 0
    assert run("type = memory\nfault = STUCK_AT_0\nbit = 11\n", stride_elf, True) == ((0x1000 << 2) | 1)
