import re
from dataclasses import dataclass

from config import CONTEXT_SENTENCES
from core.similarity import cosine_similarity, word_counts

# Metadata "page" (from PDFMinerLoader mode="page") is 0-indexed; citations
# are shown to users as 1-indexed page numbers.
PAGE_DISPLAY_OFFSET = 1
CITATION_TEMPLATE = "\n\n---\nSource (page {page}):\n{quote}"

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Sentence:
    text: str
    page: int


def split_into_sentences(text: str) -> list:
    """Split page/chunk text into a list of trimmed sentences."""
    stripped = text.strip()
    if not stripped:
        return []
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(stripped) if s.strip()]


def build_sentence_pool(documents: list) -> list:
    """
    Split the text of each retrieved Document into sentences, tagged with
    the page number of the Document they came from.

    Args:
        documents: Retrieved chunks (langchain Documents with a "page" in metadata).

    Returns:
        List of Sentence, in document order.
    """
    pool = []
    for doc in documents:
        page = doc.metadata.get("page")
        for sentence_text in split_into_sentences(doc.page_content):
            pool.append(Sentence(text=sentence_text, page=page))
    return pool


def find_hit_sentence_index(sentences: list, answer: str) -> int:
    """
    Find the sentence in the pool most similar to the generated answer.

    Args:
        sentences: Non-empty list of Sentence.
        answer: The LLM's generated answer text.

    Returns:
        Index into `sentences` of the highest-scoring ("hit") sentence.
    """
    if not sentences:
        raise ValueError("sentences must be non-empty")
    answer_counts = word_counts(answer)
    scores = [cosine_similarity(word_counts(s.text), answer_counts) for s in sentences]
    return max(range(len(sentences)), key=lambda i: scores[i])


def build_quote(sentences: list, hit_index: int, context_size: int = CONTEXT_SENTENCES):
    """
    Build a quote around the hit sentence: the hit sentence plus up to
    `context_size` sentences before and after it, restricted to sentences
    from the same page (truncated gracefully at page boundaries).

    Args:
        sentences: The full sentence pool (as returned by build_sentence_pool).
        hit_index: Index into `sentences` of the hit sentence.
        context_size: Max sentences to include on each side.

    Returns:
        (quote_text, page) tuple.
    """
    hit = sentences[hit_index]
    same_page = [(i, s) for i, s in enumerate(sentences) if s.page == hit.page]
    hit_position = next(pos for pos, (i, _) in enumerate(same_page) if i == hit_index)

    start = max(0, hit_position - context_size)
    end = min(len(same_page), hit_position + context_size + 1)
    quote_text = " ".join(s.text for _, s in same_page[start:end])
    return quote_text, hit.page


def format_citation(quote: str, page: int) -> str:
    """Render a quote block with a page-number separator line."""
    return CITATION_TEMPLATE.format(page=page + PAGE_DISPLAY_OFFSET, quote=quote)


def build_citation_block(documents: list, answer: str) -> str:
    """
    High-level entry point: pool sentences from the retrieved documents,
    identify the hit sentence supporting the answer, and render the quote
    block for it.

    Args:
        documents: Retrieved chunks (langchain Documents with a "page" in metadata).
        answer: The LLM's generated answer text.

    Returns:
        The formatted citation block, or "" if there are no sentences to cite.
    """
    sentences = build_sentence_pool(documents)
    if not sentences:
        return ""
    hit_index = find_hit_sentence_index(sentences, answer)
    quote, page = build_quote(sentences, hit_index)
    return format_citation(quote, page)
