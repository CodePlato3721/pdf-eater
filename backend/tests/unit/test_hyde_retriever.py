"""
Unit tests for backend/core/hyde_retriever.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_hyde_retriever.py -v
"""
import pytest
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from core.hyde_retriever import HydeRetriever

RAW_QUESTION = "hi"
HYPOTHETICAL_ANSWER = "H" * 500


class FakeEmbeddings(Embeddings):
    """Deterministic stand-in for OpenAIEmbeddings; no network calls. Embeds
    any text to its character length, so similarity search can be steered
    towards a document with a matching content length."""

    def embed_documents(self, texts):
        return [[float(len(t))] for t in texts]

    def embed_query(self, text):
        return [float(len(text))]


class FakeAnswer:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    """Stand-in for the chain's ChatOpenAI instance."""

    def __init__(self, answer: str = HYPOTHETICAL_ANSWER, error: Exception | None = None):
        self._answer = answer
        self._error = error

    def invoke(self, prompt):
        if self._error is not None:
            raise self._error
        return FakeAnswer(self._answer)


def make_vectorstore():
    doc_matching_question = Document(
        page_content="h" * len(RAW_QUESTION), metadata={"id": "matches-raw-question"}
    )
    doc_matching_hyde = Document(
        page_content="H" * len(HYPOTHETICAL_ANSWER), metadata={"id": "matches-hyde-answer"}
    )
    return FAISS.from_documents(
        [doc_matching_question, doc_matching_hyde], FakeEmbeddings()
    )


class TestHydeRetriever:
    def test_generates_a_hypothetical_answer_and_searches_on_its_embedding(self):
        """The retriever must embed the LLM's hypothetical answer, not the
        raw question, when running the similarity search."""
        retriever = HydeRetriever(vectorstore=make_vectorstore(), llm=FakeLLM(), k=1)

        results = retriever.invoke(RAW_QUESTION)

        assert len(results) == 1
        assert results[0].metadata["id"] == "matches-hyde-answer"

    def test_llm_failure_propagates_as_an_error(self):
        """No silent fallback to embedding the raw question: if the
        hypothetical-answer LLM call fails, the retriever call must fail
        too."""
        retriever = HydeRetriever(
            vectorstore=make_vectorstore(),
            llm=FakeLLM(error=RuntimeError("LLM unavailable")),
            k=1,
        )

        with pytest.raises(RuntimeError, match="LLM unavailable"):
            retriever.invoke(RAW_QUESTION)

    def test_respects_the_configured_k(self):
        results = HydeRetriever(vectorstore=make_vectorstore(), llm=FakeLLM(), k=2).invoke(
            RAW_QUESTION
        )

        assert len(results) == 2
