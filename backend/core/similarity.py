import math
import re
from collections import Counter

_WORD_PATTERN = re.compile(r"[a-z0-9]+")


def word_counts(text: str) -> Counter:
    """Bag-of-words vector for a piece of text: word -> occurrence count."""
    return Counter(_WORD_PATTERN.findall(text.lower()))


def cosine_similarity(a: Counter, b: Counter) -> float:
    """Cosine similarity between two bag-of-words vectors, in [0, 1]."""
    if not a or not b:
        return 0.0
    dot = sum(count * b[word] for word, count in a.items())
    norm_a = math.sqrt(sum(count * count for count in a.values()))
    norm_b = math.sqrt(sum(count * count for count in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
