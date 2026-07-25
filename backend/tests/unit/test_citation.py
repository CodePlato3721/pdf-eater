"""
Unit tests for backend/core/citation.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_citation.py -v
"""
from langchain_core.documents import Document

from core.citation import (
    Sentence,
    build_citation_block,
    build_quote,
    build_sentence_pool,
    find_hit_sentence_index,
    format_citation,
    split_into_sentences,
)


class TestSplitIntoSentences:
    """Tests for split_into_sentences()"""

    def test_splits_on_sentence_terminators(self):
        text = "The cat sat. The dog ran! Did it work?"
        assert split_into_sentences(text) == [
            "The cat sat.",
            "The dog ran!",
            "Did it work?",
        ]

    def test_empty_text_returns_empty_list(self):
        assert split_into_sentences("   ") == []


class TestBuildSentencePool:
    """Tests for build_sentence_pool()"""

    def test_pools_sentences_tagged_with_their_documents_page(self):
        documents = [
            Document(page_content="First sentence. Second sentence.", metadata={"page": 0}),
            Document(page_content="Third sentence.", metadata={"page": 1}),
        ]

        pool = build_sentence_pool(documents)

        assert pool == [
            Sentence(text="First sentence.", page=0),
            Sentence(text="Second sentence.", page=0),
            Sentence(text="Third sentence.", page=1),
        ]


class TestFindHitSentenceIndex:
    """Tests for find_hit_sentence_index()"""

    def test_picks_sentence_most_similar_to_answer(self):
        sentences = [
            Sentence(text="Bananas are yellow fruit.", page=0),
            Sentence(text="The mitochondria is the powerhouse of the cell.", page=0),
            Sentence(text="Paris is the capital of France.", page=1),
        ]

        hit_index = find_hit_sentence_index(sentences, "What is the capital of France?")

        assert sentences[hit_index].text == "Paris is the capital of France."


class TestBuildQuote:
    """Tests for build_quote()"""

    def test_includes_up_to_two_sentences_on_each_side(self):
        sentences = [
            Sentence(text="S1.", page=0),
            Sentence(text="S2.", page=0),
            Sentence(text="S3.", page=0),
            Sentence(text="S4.", page=0),
            Sentence(text="S5.", page=0),
        ]

        quote, page = build_quote(sentences, hit_index=2)

        assert quote == "S1. S2. S3. S4. S5."
        assert page == 0

    def test_truncates_when_hit_is_first_sentence_on_page(self):
        """No sentence exists before the first sentence of a page — the quote
        simply starts there instead of pulling in a previous page's text."""
        sentences = [
            Sentence(text="Prev page tail.", page=0),
            Sentence(text="First on page 1.", page=1),
            Sentence(text="Second on page 1.", page=1),
            Sentence(text="Third on page 1.", page=1),
        ]

        quote, page = build_quote(sentences, hit_index=1)

        assert quote == "First on page 1. Second on page 1. Third on page 1."
        assert page == 1

    def test_truncates_when_hit_is_last_sentence_on_page(self):
        """No sentence exists after the last sentence of a page — the quote
        simply ends there instead of pulling in the next page's text."""
        sentences = [
            Sentence(text="First on page 0.", page=0),
            Sentence(text="Second on page 0.", page=0),
            Sentence(text="Last on page 0.", page=0),
            Sentence(text="Next page head.", page=1),
        ]

        quote, page = build_quote(sentences, hit_index=2)

        assert quote == "First on page 0. Second on page 0. Last on page 0."
        assert page == 0

    def test_only_pulls_context_from_the_same_page(self):
        """Sentences from other pages must never leak into the quote, even
        when they're adjacent in the pooled list."""
        sentences = [
            Sentence(text="Page 0 tail.", page=0),
            Sentence(text="Page 1 only sentence.", page=1),
            Sentence(text="Page 2 head.", page=2),
        ]

        quote, page = build_quote(sentences, hit_index=1)

        assert quote == "Page 1 only sentence."
        assert page == 1


class TestFormatCitation:
    """Tests for format_citation()"""

    def test_renders_quote_with_one_indexed_page_separator(self):
        rendered = format_citation("Some quoted text.", page=0)

        assert "page 1" in rendered
        assert "Some quoted text." in rendered


class TestBuildCitationBlock:
    """Tests for build_citation_block() end-to-end wiring of the module."""

    def test_builds_citation_around_hit_sentence(self):
        documents = [
            Document(
                page_content="The sky is blue. Paris is the capital of France. It has the Eiffel Tower.",
                metadata={"page": 4},
            ),
        ]

        block = build_citation_block(documents, answer="France's capital is Paris.")

        assert "page 5" in block
        assert "Paris is the capital of France." in block

    def test_returns_empty_string_when_no_sentences_available(self):
        documents = [Document(page_content="   ", metadata={"page": 0})]

        assert build_citation_block(documents, answer="anything") == ""

    def test_returns_no_source_found_when_best_match_is_below_threshold(self):
        """When none of the retrieved sentences meaningfully support the
        answer, the block must say so instead of quoting the least-dissimilar
        sentence as if it were supporting evidence."""
        documents = [
            Document(
                page_content="Act third was the castle hall, and here Hagar appeared.",
                metadata={"page": 35},
            ),
        ]

        block = build_citation_block(
            documents,
            answer="Professor Friedrich Bhaer first appears when he arrives at the March family home.",
        )

        assert block == "\n\n---\nNo supporting source found in the document."
        assert "page 36" not in block
        assert "Hagar" not in block

    def test_cites_a_correct_but_short_paraphrased_answer(self):
        """PD-09: a correct, on-topic answer that only loosely echoes the
        source sentence's wording (e.g. a short factual paraphrase, not a
        near-verbatim quote) must still be cited — MIN_CITATION_SIMILARITY
        must not be so strict that it rejects legitimate answers, only
        wrong-topic ones (see the PD-07/PD-08 Hagar/Bhaer case above, whose
        score is ~0.09). Note this is a partial fix: at the chosen threshold
        (0.2) an even terser answer like "...first appears at the age of
        thirteen." (score ~0.19) still narrowly falls short and would still
        be reported as unsupported — that residual gap was accepted rather
        than lowering the threshold further, since going lower starts
        crowding the known hallucination scores (~0.09-0.12)."""
        documents = [
            Document(
                page_content=(
                    "Elizabeth or Beth, as every one called her, was a rosy, "
                    "smooth-haired, bright-eyed girl of thirteen, with a shy "
                    "manner, a timid voice, and a peaceful expression, which "
                    "was seldom disturbed."
                ),
                metadata={"page": 21},
            ),
        ]

        block = build_citation_block(
            documents,
            answer='Elizabeth "Beth" first appears as a shy, thirteen-year-old girl.',
        )

        assert "No supporting source found" not in block
        assert "page 22" in block
