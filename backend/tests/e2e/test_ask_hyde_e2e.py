"""
End-to-end test for the /api/ask flow's HyDE retrieval step (PD-10).

Hits the real OpenAI API (chat completions + embeddings) via the actual
ingestion -> create_chain -> ask() flow, no LLM fakes/mocks — needs a valid
OPENAI_API_KEY and costs a small amount. Excluded by default, run with:
    .venv\\Scripts\\python.exe -m pytest tests/e2e -m smoke -v
"""
import logging
from pathlib import Path

import pytest
from dotenv import load_dotenv

import services.state as state_module
from core.chain import create_chain
from core.embeddings import create_vectorstore
from core.loader import load_and_split
from services.qa import ask
from services.state import AppState

BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
FIXTURE_PDF = Path(__file__).resolve().parents[1] / "unit" / "fixtures" / "metamorphosis.pdf"


@pytest.mark.smoke
class TestAskExercisesHydeConversion:
    """DESIGN.md's stated acceptance check for PD-10: the /api/ask flow must
    actually ask the LLM to write a hypothetical answer (HyDE) as part of
    retrieval, not just construct a HydeRetriever that's never exercised."""

    @pytest.fixture(autouse=True)
    def _load_real_api_key(self):
        """Mirrors main.py's own load_dotenv() call: override=True is
        required because a stale OPENAI_API_KEY already set in the OS
        environment would otherwise take precedence over .env."""
        load_dotenv(BACKEND_ENV_PATH, override=True)

    @pytest.fixture
    def app_state(self, tmp_path, monkeypatch):
        """A fresh AppState with history persistence redirected to a temp
        file, so the real ask() call doesn't write to data/history.json."""
        monkeypatch.setattr(state_module, "HISTORY_PATH", str(tmp_path / "history.json"))
        return AppState()

    def test_ask_sends_a_hyde_hypothetical_answer_request_before_answering(
        self, app_state, caplog
    ):
        """Runs a real ingestion + ask() against the Metamorphosis fixture PDF
        and inspects the actual HTTP request bodies logged by
        core/http_logging.py: one of them must be the HyDE prompt asking the
        LLM for a hypothetical passage, proving the conversion really
        happens inside the ask flow rather than being dead code."""
        caplog.set_level(logging.INFO, logger="pdf_eater.openai_http")
        chunks = load_and_split([FIXTURE_PDF.read_bytes()])
        vectorstore = create_vectorstore(chunks)
        app_state.chain = create_chain(vectorstore)

        ask("What happens to Gregor Samsa?", app_state)

        hyde_requests = [
            record.getMessage()
            for record in caplog.records
            if "[LLM] REQUEST" in record.getMessage()
            and "hypothetical passage" in record.getMessage()
        ]
        assert len(hyde_requests) >= 1
