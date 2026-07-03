"""Text statistics helpers. Word-count has a bug; the sentiment path needs an
optional third-party package (`vaderSentiment`) that is NOT installed here."""


def word_count(text):
    # BUG: splits on spaces only, so newline-separated words are miscounted.
    return len(text.split(" "))


def char_histogram(text):
    hist = {}
    for ch in text:
        if ch.isalpha():
            hist[ch.lower()] = hist.get(ch.lower(), 0) + 1
    return hist


def sentiment(text):
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # not installed

    return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
