import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats_util import normalize, moving_average, smooth_series


def test_normalize_basic():
    assert normalize([0, 5, 10]) == [0.0, 0.5, 1.0]


def test_normalize_flat():
    assert normalize([4, 4]) == [0.0, 0.0]


def test_moving_average_head():
    # Docstring: "the first window-1 entries average what exists".
    # For [3, 6, 9] with window 3: head entries should be 3.0 and 4.5.
    assert moving_average([3, 6, 9], 3) == [3.0, 4.5, 6.0]


def test_smooth_series_report_values():
    # Golden values for the monthly report plot (window=3).
    assert smooth_series([1, 2, 3, 4], 3) == [0.333, 1.0, 2.0, 3.0]
