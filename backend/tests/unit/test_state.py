"""
Unit tests for backend/services/state.py (pure state container)

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_state.py -v
"""
import json

from unittest.mock import patch

import services.state as state_module
from services.state import AppState


class TestSaveHistory:
    """Tests for AppState.save_history()"""

    def test_save_history_writes_json_and_creates_parent_dir(self, tmp_path):
        """save_history() writes chat_history as JSON, creating the data dir."""
        history_file = tmp_path / "data" / "history.json"

        with patch.object(state_module, "HISTORY_PATH", str(history_file)):
            st = AppState()
            st.chat_history = [["hello", "hi"]]
            st.save_history()

        assert json.loads(history_file.read_text(encoding="utf-8")) == [["hello", "hi"]]


class TestLoadHistory:
    """Tests for AppState.load_history()"""

    def test_load_history_populates_chat_history_from_json(self, tmp_path):
        """load_history() populates chat_history from history.json when the file exists."""
        history_file = tmp_path / "history.json"
        history_data = [["hello", "hi"]]
        history_file.write_text(json.dumps(history_data), encoding="utf-8")

        with patch.object(state_module, "HISTORY_PATH", str(history_file)):
            st = AppState()
            st.load_history()

        assert st.chat_history == history_data

    def test_load_history_keeps_empty_history_when_file_missing(self, tmp_path):
        """load_history() leaves chat_history as [] when history.json is absent."""
        with patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")):
            st = AppState()
            st.load_history()

        assert st.chat_history == []

    def test_load_history_resets_to_empty_on_corrupt_file(self, tmp_path):
        """load_history() falls back to [] instead of raising on invalid JSON."""
        history_file = tmp_path / "history.json"
        history_file.write_text("{not valid json", encoding="utf-8")

        with patch.object(state_module, "HISTORY_PATH", str(history_file)):
            st = AppState()
            st.load_history()

        assert st.chat_history == []
