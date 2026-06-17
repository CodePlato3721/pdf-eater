"""
Unit tests for backend/state.py

Run from the project root:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_state.py -v
"""
import json

import pytest
from unittest.mock import MagicMock, patch

import state as state_module
from state import AppState



class TestRestore:
    """Tests for AppState.restore()"""

    def test_restore_calls_load_and_create_when_index_exists(self, tmp_path):
        """restore() calls load_vectorstore and create_chain when faiss_index dir exists,
        and assigns the returned chain to self.chain."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        fake_vectorstore = MagicMock()
        fake_chain = MagicMock()

        with patch.object(state_module, "FAISS_INDEX_PATH", str(index_dir)), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(state_module, "load_vectorstore", return_value=fake_vectorstore) as mock_load, \
             patch.object(state_module, "create_chain", return_value=fake_chain) as mock_create:

            st = AppState()
            st.restore()

        mock_load.assert_called_once_with(str(index_dir))
        mock_create.assert_called_once_with(fake_vectorstore)
        assert st.chain is fake_chain

    def test_restore_chain_is_none_when_faiss_index_missing(self, tmp_path):
        """restore() leaves chain as None when faiss_index dir does not exist."""
        with patch.object(state_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(state_module, "load_vectorstore") as mock_load, \
             patch.object(state_module, "create_chain") as mock_create:

            st = AppState()
            st.restore()

        mock_load.assert_not_called()
        mock_create.assert_not_called()
        assert st.chain is None

    def test_restore_chain_is_none_when_faiss_corrupted(self, tmp_path):
        """restore() sets chain to None and does not raise when load_vectorstore throws."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        with patch.object(state_module, "FAISS_INDEX_PATH", str(index_dir)), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(state_module, "load_vectorstore", side_effect=Exception("corrupt")), \
             patch.object(state_module, "create_chain") as mock_create:

            st = AppState()
            st.restore()  # must not raise

        mock_create.assert_not_called()
        assert st.chain is None

    def test_restore_loads_chat_history_from_json(self, tmp_path):
        """restore() populates chat_history from history.json when the file exists."""
        history_file = tmp_path / "history.json"
        history_data = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        history_file.write_text(json.dumps(history_data), encoding="utf-8")

        with patch.object(state_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(history_file)):

            st = AppState()
            st.restore()

        assert st.chat_history == history_data

    def test_restore_empty_chat_history_when_no_history_file(self, tmp_path):
        """restore() leaves chat_history as [] when history.json is absent."""
        with patch.object(state_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")):

            st = AppState()
            st.restore()

        assert st.chat_history == []
