import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textstats import word_count, char_histogram, sentiment


def test_word_count_spaces():
    assert word_count("one two three") == 3


def test_word_count_newlines():
    # Words separated by newlines must still count. (This fails until word_count is fixed.)
    assert word_count("one\ntwo three") == 3


def test_char_histogram():
    assert char_histogram("aA b") == {"a": 2, "b": 1}


def test_sentiment_positive():
    # Requires vaderSentiment, which is not installed in this environment.
    assert sentiment("I love this, it is wonderful") > 0
