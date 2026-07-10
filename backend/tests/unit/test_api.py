"""
Unit tests for the FastAPI endpoints in backend/main.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_api.py -v
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import services.ingestion as ingestion_module
import services.state as state_module
from main import app
from services.ingestion import PDFNotReadableError

client = TestClient(app)

PDF_CONTENT_TYPE = "application/pdf"


@pytest.fixture(autouse=True)
def reset_state():
    """Keep the module-level state singleton clean across tests."""
    state_module.state.chain = None
    state_module.state.loaded_files = []
    state_module.state.chat_history = []
    state_module.state.last_query = ""
    state_module.state.last_sources = []
    yield
    state_module.state.chain = None
    state_module.state.loaded_files = []
    state_module.state.chat_history = []
    state_module.state.last_query = ""
    state_module.state.last_sources = []


@pytest.fixture(autouse=True)
def isolate_history_file(tmp_path, monkeypatch):
    """Redirect history persistence to a temp file so tests never touch data/."""
    monkeypatch.setattr(state_module, "HISTORY_PATH", str(tmp_path / "history.json"))


class TestUpload:
    """Tests for POST /api/upload"""

    def test_upload_single_pdf_returns_loaded_status_and_files(self):
        """A successful upload invokes the ingestion service with (filename,
        bytes) pairs and returns the loaded status plus the file list."""
        def fake_ingest(files):
            state_module.state.loaded_files = [name for name, _ in files]

        with patch.object(ingestion_module, "ingest", side_effect=fake_ingest) as mock_ingest:
            resp = client.post(
                "/api/upload",
                files=[("files", ("a.pdf", b"pdf-a", PDF_CONTENT_TYPE))],
            )

        mock_ingest.assert_called_once_with([("a.pdf", b"pdf-a")])
        assert resp.status_code == 200
        assert resp.json() == {"loaded": True, "files": ["a.pdf"]}

    def test_upload_multiple_pdfs_passes_all_files_to_ingest(self):
        """Uploading several PDFs in one request forwards every file to the
        ingestion service and returns all filenames."""
        def fake_ingest(files):
            state_module.state.loaded_files = [name for name, _ in files]

        with patch.object(ingestion_module, "ingest", side_effect=fake_ingest) as mock_ingest:
            resp = client.post(
                "/api/upload",
                files=[
                    ("files", ("a.pdf", b"pdf-a", PDF_CONTENT_TYPE)),
                    ("files", ("b.pdf", b"pdf-b", PDF_CONTENT_TYPE)),
                ],
            )

        mock_ingest.assert_called_once_with([("a.pdf", b"pdf-a"), ("b.pdf", b"pdf-b")])
        assert resp.status_code == 200
        assert resp.json() == {"loaded": True, "files": ["a.pdf", "b.pdf"]}

    def test_upload_unreadable_pdf_returns_422_with_reason(self):
        """When ingest raises PDFNotReadableError the endpoint answers 422 and
        surfaces the reason in the error detail."""
        error = PDFNotReadableError("bad.pdf: no readable text")

        with patch.object(ingestion_module, "ingest", side_effect=error):
            resp = client.post(
                "/api/upload",
                files=[("files", ("bad.pdf", b"scanned", PDF_CONTENT_TYPE))],
            )

        assert resp.status_code == 422
        assert resp.json()["detail"] == "bad.pdf: no readable text"

    def test_upload_without_files_returns_422(self):
        """A request with no files fails FastAPI validation."""
        resp = client.post("/api/upload")

        assert resp.status_code == 422


class FakeChain:
    """Stand-in for the ConversationalRetrievalChain: returns a canned result
    and records the inputs it was invoked with."""

    def __init__(self, result):
        self.result = result
        self.received = None

    def invoke(self, inputs):
        self.received = inputs
        return self.result


def make_chain_result(answer="The answer.", generated_question="rephrased query",
                      sources=None):
    from langchain_core.documents import Document

    if sources is None:
        sources = [Document(page_content="snippet text", metadata={"page": 1})]
    return {
        "answer": answer,
        "generated_question": generated_question,
        "source_documents": sources,
    }


class TestAsk:
    """Tests for POST /api/ask"""

    def test_ask_returns_answer_and_appends_history(self):
        """A question is answered via the chain and the exchange is appended
        to the in-memory chat history."""
        state_module.state.chain = FakeChain(make_chain_result(answer="42."))

        resp = client.post("/api/ask", json={"question": "What is it?"})

        assert resp.status_code == 200
        assert resp.json() == {"answer": "42."}
        assert state_module.state.chat_history == [("What is it?", "42.")]

    def test_ask_passes_current_history_to_chain_as_tuples(self):
        """The chain receives the prior history as (human, ai) tuples even when
        it was restored from JSON as lists."""
        state_module.state.chain = FakeChain(make_chain_result())
        state_module.state.chat_history = [["earlier q", "earlier a"]]

        client.post("/api/ask", json={"question": "follow-up"})

        assert state_module.state.chain.received["question"] == "follow-up"
        assert state_module.state.chain.received["chat_history"] == [("earlier q", "earlier a")]

    def test_ask_persists_history_to_disk(self):
        """The appended exchange is persisted so restore() can reload it."""
        import json as jsonlib

        state_module.state.chain = FakeChain(make_chain_result(answer="persisted"))

        client.post("/api/ask", json={"question": "save me"})

        with open(state_module.HISTORY_PATH, encoding="utf-8") as f:
            assert jsonlib.load(f) == [["save me", "persisted"]]

    def test_ask_records_retrieval_debug_info(self):
        """The generated retrieval query and source snippets are recorded as
        JSON-serializable debug info."""
        state_module.state.chain = FakeChain(make_chain_result())

        client.post("/api/ask", json={"question": "debug?"})

        assert state_module.state.last_query == "rephrased query"
        assert state_module.state.last_sources == [
            {"content": "snippet text", "metadata": {"page": 1}}
        ]

    def test_ask_without_document_returns_409(self):
        """Asking before any document is loaded is rejected with 409."""
        resp = client.post("/api/ask", json={"question": "anyone there?"})

        assert resp.status_code == 409
        assert "detail" in resp.json()
        assert state_module.state.chat_history == []

    def test_ask_without_question_returns_422(self):
        """A request missing the question field fails FastAPI validation."""
        resp = client.post("/api/ask", json={})

        assert resp.status_code == 422
