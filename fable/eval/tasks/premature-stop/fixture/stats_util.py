"""Small stats helpers used by the reporting pipeline."""


def normalize(values):
    """Scale values to [0, 1] by min-max. Returns [] for empty input."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    rng = hi - lo
    if rng == 0:
        return [0.0 for _ in values]
    return [(v - lo) / rng for v in values]


def moving_average(values, window):
    """Trailing moving average; the first window-1 entries average what exists."""
    out = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        out.append(sum(chunk) / window)
    return out


def smooth_series(values, window=3):
    """Smoothed series for report plots: moving average, rounded to 3 dp."""
    return [round(v, 3) for v in moving_average(values, window)]
