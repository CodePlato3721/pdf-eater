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


class TestClearHistory:
    """Tests for AppState.clear_history()"""

    def test_clear_history_empties_memory_and_persisted_file(self, tmp_path):
        """clear_history() resets chat_history and clears the persisted file."""
        history_file = tmp_path / "history.json"
        history_file.write_text(json.dumps([["hello", "hi"]]), encoding="utf-8")

        with patch.object(state_module, "HISTORY_PATH", str(history_file)):
            st = AppState()
            st.chat_history = [["hello", "hi"]]
            st.clear_history()

        assert st.chat_history == []
        assert json.loads(history_file.read_text(encoding="utf-8")) == []


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


class TestSaveUploadedFiles:
    """Tests for AppState.save_uploaded_files()"""

    def test_save_uploaded_files_writes_json_and_creates_parent_dir(self, tmp_path):
        """save_uploaded_files() writes loaded_files as JSON, creating the data dir."""
        files_file = tmp_path / "data" / "uploaded_files.json"

        with patch.object(state_module, "UPLOADED_FILES_PATH", str(files_file)):
            st = AppState()
            st.loaded_files = ["a.pdf", "b.pdf"]
            st.save_uploaded_files()

        assert json.loads(files_file.read_text(encoding="utf-8")) == ["a.pdf", "b.pdf"]

    def test_save_uploaded_files_replaces_not_appends_previous_contents(self, tmp_path):
        """save_uploaded_files() fully replaces the persisted file list rather than appending."""
        files_file = tmp_path / "uploaded_files.json"

        with patch.object(state_module, "UPLOADED_FILES_PATH", str(files_file)):
            st = AppState()
            st.loaded_files = ["a.pdf"]
            st.save_uploaded_files()
            st.loaded_files = ["c.pdf"]
            st.save_uploaded_files()

        assert json.loads(files_file.read_text(encoding="utf-8")) == ["c.pdf"]


class TestLoadUploadedFiles:
    """Tests for AppState.load_uploaded_files()"""

    def test_load_uploaded_files_populates_loaded_files_from_json(self, tmp_path):
        """load_uploaded_files() populates loaded_files from uploaded_files.json when it exists."""
        files_file = tmp_path / "uploaded_files.json"
        files_data = ["a.pdf", "b.pdf"]
        files_file.write_text(json.dumps(files_data), encoding="utf-8")

        with patch.object(state_module, "UPLOADED_FILES_PATH", str(files_file)):
            st = AppState()
            st.load_uploaded_files()

        assert st.loaded_files == files_data

    def test_load_uploaded_files_keeps_empty_list_when_file_missing(self, tmp_path):
        """load_uploaded_files() leaves loaded_files as [] when uploaded_files.json is absent,
        without creating the file."""
        files_file = tmp_path / "uploaded_files.json"

        with patch.object(state_module, "UPLOADED_FILES_PATH", str(files_file)):
            st = AppState()
            st.load_uploaded_files()

        assert st.loaded_files == []
        assert not files_file.exists()

    def test_load_uploaded_files_resets_to_empty_on_corrupt_file(self, tmp_path):
        """load_uploaded_files() falls back to [] instead of raising on invalid JSON."""
        files_file = tmp_path / "uploaded_files.json"
        files_file.write_text("{not valid json", encoding="utf-8")

        with patch.object(state_module, "UPLOADED_FILES_PATH", str(files_file)):
            st = AppState()
            st.load_uploaded_files()

        assert st.loaded_files == []
