"""Parse a 1-based inclusive range string like "3-7" into a list of indices."""


def parse_range(spec):
    """
    "3-7"  -> [3, 4, 5, 6, 7]
    "5"    -> [5]
    "  2 - 4 " -> [2, 3, 4]
    Raises ValueError on malformed input or when start > end.
    """
    spec = spec.strip()
    if "-" in spec:
        a, b = spec.split("-", 1)
        start, end = int(a.strip()), int(b.strip())
        if start > end:
            raise ValueError(f"start > end in {spec!r}")
        return list(range(start, end + 1))
    return [int(spec)]


def select(rows, spec):
    """Return the rows whose 1-based position is in the range spec."""
    idx = set(parse_range(spec))
    return [row for i, row in enumerate(rows, start=1) if i in idx]
