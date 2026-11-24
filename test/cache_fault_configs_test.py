import itertools
import pathlib
import sys

directory = pathlib.Path(sys.argv[1])
widths = {"valid": 1, "modified": 1, "id": 1, "tag": 25}
expected = set(itertools.chain.from_iterable(
    ((field, bit, fault, rate)
     for bit in range(width)
     for fault in ("STUCK_AT_0", "STUCK_AT_1", "BIT_FLIP")
     for rate in (0.5, 1.0))
    for field, width in widths.items()))
actual = set()
for path in directory.glob("*.txt"):
    properties = dict(line.split(" = ", 1) for line in path.read_text().splitlines())
    assert properties.pop("type") == "cache", path
    config = (properties.pop("field"), int(properties.pop("bit")),
              properties.pop("fault"), float(properties.pop("rate")))
    assert not properties and config not in actual, path
    actual.add(config)
assert actual == expected, (expected - actual, actual - expected)
