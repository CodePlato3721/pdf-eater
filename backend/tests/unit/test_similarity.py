"""
Unit tests for backend/core/similarity.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_similarity.py -v
"""
import pytest

from core.similarity import cosine_similarity, word_counts


class TestWordCounts:
    """Tests for word_counts()"""

    def test_counts_words_case_insensitively(self):
        assert word_counts("Paris is the capital of Paris") == {
            "paris": 2, "is": 1, "the": 1, "capital": 1, "of": 1,
        }

    def test_ignores_punctuation(self):
        assert word_counts("Wait, what?!") == {"wait": 1, "what": 1}


class TestCosineSimilarity:
    """Tests for cosine_similarity()"""

    def test_identical_text_scores_one(self):
        text = word_counts("Paris is the capital of France.")
        assert cosine_similarity(text, text) == pytest.approx(1.0)

    def test_disjoint_text_scores_zero(self):
        a = word_counts("Bananas are yellow.")
        b = word_counts("Paris is the capital of France.")
        assert cosine_similarity(a, b) == 0.0

    def test_partial_overlap_scores_between_zero_and_one(self):
        a = word_counts("Paris is the capital of France.")
        b = word_counts("Paris is beautiful in the spring.")
        score = cosine_similarity(a, b)
        assert 0.0 < score < 1.0

    def test_empty_input_scores_zero(self):
        assert cosine_similarity(word_counts(""), word_counts("anything")) == 0.0
