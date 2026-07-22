"""
Unit tests for backend/core/loader.py.

Run from the backend/ directory:
    ../.venv/Scripts/python.exe -m pytest tests/unit/test_loader.py -v
"""
import os

import pytest

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "fixtures", "metamorphosis.pdf")


@pytest.fixture(scope="module")
def real_pdf_chunks():
    """Run load_and_split() once against the real Metamorphosis PDF and share
    the result across tests."""
    from core import loader

    with open(FIXTURE_PDF, "rb") as f:
        pdf_bytes = f.read()
    return loader.load_and_split([pdf_bytes])


class TestLoadAndSplitRealPdf:
    """Tests for load_and_split() against a real multi-page PDF (no mocking
    of PDFMinerLoader/RecursiveCharacterTextSplitter) — verifies the actual
    reading result, not just that internal calls were made."""

    def test_produces_non_empty_page_tagged_chunks(self, real_pdf_chunks):
        assert len(real_pdf_chunks) > 0
        for chunk in real_pdf_chunks:
            assert isinstance(chunk.metadata.get("page"), int)
            assert chunk.metadata["page"] >= 0
            assert chunk.page_content.strip() != ""

    def test_chunks_span_multiple_pages(self, real_pdf_chunks):
        """mode="page" must actually take effect: a 26-page book collapsed
        into mode="single" would produce chunks with no page number at all."""
        pages = {chunk.metadata["page"] for chunk in real_pdf_chunks}
        assert len(pages) > 1

    def test_chunk_content_matches_known_book_text(self, real_pdf_chunks):
        """Sanity-check the extracted text is really this book's content, and
        that the matching chunk's page number lands near the known page."""
        matches = [c for c in real_pdf_chunks if "chief clerk" in c.page_content.lower()]

        assert len(matches) > 0
        assert any(2 <= c.metadata["page"] <= 6 for c in matches)
