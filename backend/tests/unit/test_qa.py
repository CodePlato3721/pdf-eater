"""
Unit tests for backend/services/qa.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_qa.py -v
"""
import json

import pytest
from langchain_core.documents import Document

import services.state as state_module
from core.citation import build_citation_block
from services.qa import NoDocumentLoadedError, ask
from services.state import AppState


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
    if sources is None:
        sources = [Document(page_content="snippet text", metadata={"page": 1})]
    return {
        "answer": answer,
        "generated_question": generated_question,
        "source_documents": sources,
    }


@pytest.fixture
def app_state(tmp_path, monkeypatch):
    """A fresh AppState with history persistence redirected to a temp file."""
    monkeypatch.setattr(state_module, "HISTORY_PATH", str(tmp_path / "history.json"))
    return AppState()


class TestAsk:
    """Tests for qa.ask()"""

    def test_ask_returns_answer_and_appends_history(self, app_state):
        """A question is answered via the chain and the exchange (including
        its appended citation block) is appended to the in-memory chat history."""
        sources = [Document(page_content="Fact one. Fact two.", metadata={"page": 0})]
        app_state.chain = FakeChain(make_chain_result(answer="42.", sources=sources))

        answer = ask("What is it?", app_state)

        assert answer == "42." + build_citation_block(sources, "42.")
        assert app_state.chat_history == [("What is it?", answer)]

    def test_ask_passes_current_history_to_chain_as_tuples(self, app_state):
        """The chain receives the prior history as (human, ai) tuples even when
        it was restored from JSON as lists."""
        app_state.chain = FakeChain(make_chain_result())
        app_state.chat_history = [["earlier q", "earlier a"]]

        ask("follow-up", app_state)

        assert app_state.chain.received["question"] == "follow-up"
        assert app_state.chain.received["chat_history"] == [("earlier q", "earlier a")]

    def test_ask_persists_history_to_disk(self, app_state):
        """The appended exchange, including its citation block, is persisted
        so restore() can reload it."""
        app_state.chain = FakeChain(make_chain_result(answer="persisted"))

        answer = ask("save me", app_state)

        with open(state_module.HISTORY_PATH, encoding="utf-8") as f:
            assert json.load(f) == [["save me", answer]]

    def test_ask_records_retrieval_debug_info(self, app_state):
        """The generated retrieval query and source snippets are recorded as
        JSON-serializable debug info."""
        app_state.chain = FakeChain(make_chain_result())

        ask("debug?", app_state)

        assert app_state.last_query == "rephrased query"
        assert app_state.last_sources == [
            {"content": "snippet text", "metadata": {"page": 1}}
        ]

    def test_ask_without_document_raises_and_leaves_history_untouched(self, app_state):
        """Asking before any document is loaded raises NoDocumentLoadedError."""
        with pytest.raises(NoDocumentLoadedError):
            ask("anyone there?", app_state)

        assert app_state.chat_history == []


class TestAskCitation:
    """Tests for the source-quote citation block ask() appends to the answer."""

    def test_appends_citation_block_for_the_supporting_sentence(self, app_state):
        """The sentence in the retrieved chunks most similar to the answer is
        quoted, with a 1-indexed page separator, after the answer text."""
        sources = [
            Document(
                page_content="The sky is blue. Paris is the capital of France. It has a tower.",
                metadata={"page": 4},
            )
        ]
        app_state.chain = FakeChain(
            make_chain_result(answer="Paris is the capital.", sources=sources)
        )

        answer = ask("What is the capital of France?", app_state)

        assert "Source (page 5):" in answer
        assert "Paris is the capital of France." in answer

    def test_no_citation_appended_when_retrieved_chunks_have_no_sentences(self, app_state):
        """If the retrieved chunks contain no citable text, the answer is
        returned unchanged."""
        sources = [Document(page_content="   ", metadata={"page": 0})]
        app_state.chain = FakeChain(
            make_chain_result(answer="No support available.", sources=sources)
        )

        answer = ask("anything?", app_state)

        assert answer == "No support available."
