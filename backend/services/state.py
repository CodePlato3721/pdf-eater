import json
import logging
import os

from config import HISTORY_PATH

logger = logging.getLogger(__name__)


class AppState:
    """Pure session-state container: the QA chain, chat history, loaded files
    and retrieval debug info, plus persistence of its own history."""

    def __init__(self):
        self.chain = None
        self.chat_history: list = []
        self.loaded_files: list[str] = []
        self.last_query: str = ""
        self.last_sources: list[dict] = []

    def save_history(self) -> None:
        """Persist chat_history to HISTORY_PATH, creating the parent dir if needed."""
        parent_dir = os.path.dirname(HISTORY_PATH)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.chat_history, f, ensure_ascii=False)

    def load_history(self) -> None:
        """Reload chat_history from HISTORY_PATH; falls back to [] on errors."""
        if os.path.isfile(HISTORY_PATH):
            try:
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    self.chat_history = json.load(f)
            except Exception as exc:
                logger.error("Failed to restore chat history: %s", exc)
                self.chat_history = []


state = AppState()
