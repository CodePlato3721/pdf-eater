"""
Unit tests for backend/core/chain.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_chain.py -v

The smoke test in TestQAPromptSmoke hits the real OpenAI API and is excluded
by default (see the root pyproject.toml `addopts`/`markers`). Run it with:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_chain.py -m smoke -v
"""
from pathlib import Path

import pytest
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI

from config import MODEL_NAME
from core.chain import NOT_FOUND_ANSWER, QA_PROMPT, create_chain

BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class FakeEmbeddings(Embeddings):
    """Deterministic stand-in for OpenAIEmbeddings; no network calls."""

    def embed_documents(self, texts):
        return [[float(len(t))] for t in texts]

    def embed_query(self, text):
        return [float(len(text))]


def make_vectorstore():
    return FAISS.from_documents(
        [Document(page_content="hello world", metadata={"page": 0})],
        FakeEmbeddings(),
    )


class TestCreateChain:
    """Tests that create_chain() wires in the strict, context-only QA prompt."""

    def test_uses_the_strict_qa_prompt(self):
        """The combine-docs step must use QA_PROMPT, not LangChain's default
        (weak) 'if you don't know, say you don't know' prompt."""
        qa = create_chain(make_vectorstore())

        assert qa.combine_docs_chain.llm_chain.prompt is QA_PROMPT

    def test_prompt_forbids_outside_knowledge_and_defines_fallback_answer(self):
        """The prompt text must explicitly forbid answering from the model's
        own knowledge and give an exact fallback answer for unsupported
        questions, since the default prompt's soft wording let the LLM
        hallucinate answers from outside the retrieved context."""
        rendered = QA_PROMPT.format(context="some context", question="some question")

        assert "ONLY" in rendered
        assert "outside" in rendered.lower()
        assert NOT_FOUND_ANSWER in rendered


@pytest.mark.smoke
class TestQAPromptSmoke:
    """Confirms the model actually obeys QA_PROMPT, not just that it's wired
    in correctly. Makes one real, minimal-token ChatOpenAI call (no
    embeddings/ingestion) — needs a valid OPENAI_API_KEY and costs a
    fraction of a cent. Excluded from the default test run."""

    @pytest.fixture(autouse=True)
    def _load_real_api_key(self):
        """Mirrors main.py's own load_dotenv() call: override=True is
        required because a stale OPENAI_API_KEY already set in the OS
        environment would otherwise take precedence over .env."""
        load_dotenv(BACKEND_ENV_PATH, override=True)

    def test_model_declines_to_answer_from_outside_the_given_context(self):
        """Reproduces PD-08: with context that never mentions the question's
        subject, the model must fall back to NOT_FOUND_ANSWER instead of
        answering from its own training knowledge."""
        llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
        prompt = QA_PROMPT.format(
            context=(
                "Meg, Jo, Beth, and Amy perform a play called 'The Vampire' "
                "for their neighbors on Christmas Eve."
            ),
            question="When does Professor Friedrich Bhaer first appear?",
        )

        response = llm.invoke(prompt)

        assert NOT_FOUND_ANSWER in response.content
