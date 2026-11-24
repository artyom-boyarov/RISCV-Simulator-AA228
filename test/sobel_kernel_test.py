import os
import pathlib
import re
import subprocess
import sys
import tempfile

compiler, simulator, root_arg = sys.argv[1:]
root = pathlib.Path(root_arg)
width = 16
image = [[(13*x + 17*y + ((x ^ y) << 3) + (37 if x > y else 0)) & 255
          for x in range(width)] for y in range(width)]
gx_weights = ((-1, 0, 1), (-2, 0, 2), (-1, 0, 1))
gy_weights = ((-1, -2, -1), (0, 0, 0), (1, 2, 1))
edges = [[0] * width for _ in range(width)]
for y in range(1, width - 1):
    for x in range(1, width - 1):
        gx = sum(image[y+dy-1][x+dx-1] * gx_weights[dy][dx]
                 for dy in range(3) for dx in range(3))
        gy = sum(image[y+dy-1][x+dx-1] * gy_weights[dy][dx]
                 for dy in range(3) for dx in range(3))
        edges[y][x] = min(255, (abs(gx) + abs(gy)) // 2)

fingerprint = 0x13579bdf
for row in edges:
    for pixel in row:
        fingerprint = (((fingerprint << 5) | (fingerprint >> 27)) & 0xffffffff) ^ pixel
expected = fingerprint & 0xfff
assert expected == 1690

with tempfile.TemporaryDirectory() as directory:
    elf = pathlib.Path(directory) / "sobel.riscv"
    subprocess.run([str(root / "compile-riscv.sh"), str(root / "kernels/stress/sobel_image.c"), str(elf)],
                   env=dict(os.environ, RISCV_GCC=compiler), cwd=directory, check=True)
    for extra in ([], ["--no-cache"]):
        result = subprocess.run([simulator, str(elf), "-q", *extra], cwd=directory,
                                text=True, capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr[-2000:]
        match = re.search(r"Program return value:\s*(-?\d+)", result.stdout)
        assert match and int(match.group(1)) == expected, result.stdout
