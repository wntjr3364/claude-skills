import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parse_range import parse_range, select

ROWS = ["a", "b", "c", "d", "e"]  # 1-based positions 1..5


def test_parse_basic():
    assert parse_range("3-7") == [3, 4, 5, 6, 7]
    assert parse_range("5") == [5]
    assert parse_range(" 2 - 4 ") == [2, 3, 4]


def test_select_is_one_based():
    # Documented contract: positions are 1-based.
    assert select(ROWS, "1") == ["a"]
    assert select(ROWS, "2-4") == ["b", "c", "d"]


def test_start_gt_end_raises():
    import pytest
    with pytest.raises(ValueError):
        parse_range("7-3")
