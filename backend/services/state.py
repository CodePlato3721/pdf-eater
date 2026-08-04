from config import HISTORY_PATH, UPLOADED_FILES_PATH
from utils.file_utils import load_json, save_json


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
        save_json(HISTORY_PATH, self.chat_history)

    def clear_history(self) -> None:
        """Reset chat_history and persist it, clearing the history file too."""
        self.chat_history = []
        self.save_history()

    def load_history(self) -> None:
        """Reload chat_history from HISTORY_PATH; falls back to [] on errors."""
        self.chat_history = load_json(HISTORY_PATH, [])

    def save_uploaded_files(self) -> None:
        """Persist loaded_files to UPLOADED_FILES_PATH, fully replacing its contents."""
        save_json(UPLOADED_FILES_PATH, self.loaded_files)

    def load_uploaded_files(self) -> None:
        """Reload loaded_files from UPLOADED_FILES_PATH; falls back to [] if the
        file is missing or on read error."""
        self.loaded_files = load_json(UPLOADED_FILES_PATH, [])


state = AppState()
