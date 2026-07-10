"""
Unit tests for backend/services/ingestion.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_ingestion.py -v
"""
import json

import pytest
from unittest.mock import MagicMock, patch

import services.ingestion as ingestion_module
import services.state as state_module
from services.ingestion import PDFNotReadableError, ingest, restore
from services.state import AppState


class TestRestore:
    """Tests for ingestion.restore()"""

    def test_restore_calls_load_and_create_when_index_exists(self, tmp_path):
        """restore() calls load_vectorstore and create_chain when faiss_index dir exists,
        and assigns the returned chain to the state."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        fake_vectorstore = MagicMock()
        fake_chain = MagicMock()

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(index_dir)), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "load_vectorstore", return_value=fake_vectorstore) as mock_load, \
             patch.object(ingestion_module, "create_chain", return_value=fake_chain) as mock_create:

            st = AppState()
            restore(app_state=st)

        mock_load.assert_called_once_with(str(index_dir))
        mock_create.assert_called_once_with(fake_vectorstore)
        assert st.chain is fake_chain

    def test_restore_chain_is_none_when_faiss_index_missing(self, tmp_path):
        """restore() leaves chain as None when faiss_index dir does not exist."""
        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "load_vectorstore") as mock_load, \
             patch.object(ingestion_module, "create_chain") as mock_create:

            st = AppState()
            restore(app_state=st)

        mock_load.assert_not_called()
        mock_create.assert_not_called()
        assert st.chain is None

    def test_restore_chain_is_none_when_faiss_corrupted(self, tmp_path):
        """restore() sets chain to None and does not raise when load_vectorstore throws."""
        index_dir = tmp_path / "faiss_index"
        index_dir.mkdir()

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(index_dir)), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "load_vectorstore", side_effect=Exception("corrupt")), \
             patch.object(ingestion_module, "create_chain") as mock_create:

            st = AppState()
            restore(app_state=st)  # must not raise

        mock_create.assert_not_called()
        assert st.chain is None

    def test_restore_loads_chat_history_from_json(self, tmp_path):
        """restore() populates chat_history from history.json when the file exists."""
        history_file = tmp_path / "history.json"
        history_data = [["hello", "hi"]]
        history_file.write_text(json.dumps(history_data), encoding="utf-8")

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(history_file)):

            st = AppState()
            restore(app_state=st)

        assert st.chat_history == history_data

    def test_restore_empty_chat_history_when_no_history_file(self, tmp_path):
        """restore() leaves chat_history as [] when history.json is absent."""
        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "nonexistent")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")):

            st = AppState()
            restore(app_state=st)

        assert st.chat_history == []


class TestIngest:
    """Tests for ingestion.ingest()"""

    def test_ingest_builds_chain_and_updates_state(self, tmp_path):
        """ingest() runs load_and_split -> create_vectorstore -> create_chain and
        updates chain, loaded_files and resets chat_history."""
        fake_docs = [MagicMock()]
        fake_vectorstore = MagicMock()
        fake_chain = MagicMock()

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "faiss_index")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "is_readable", return_value=(True, "")), \
             patch.object(ingestion_module, "load_and_split", return_value=fake_docs) as mock_split, \
             patch.object(ingestion_module, "create_vectorstore", return_value=fake_vectorstore) as mock_vs, \
             patch.object(ingestion_module, "save_vectorstore"), \
             patch.object(ingestion_module, "create_chain", return_value=fake_chain) as mock_chain:

            st = AppState()
            st.chat_history = [("old question", "old answer")]
            ingest([("a.pdf", b"pdf-a"), ("b.pdf", b"pdf-b")], app_state=st)

        mock_split.assert_called_once_with([b"pdf-a", b"pdf-b"])
        mock_vs.assert_called_once_with(fake_docs)
        mock_chain.assert_called_once_with(fake_vectorstore)
        assert st.chain is fake_chain
        assert st.loaded_files == ["a.pdf", "b.pdf"]
        assert st.chat_history == []

    def test_ingest_persists_index_and_history(self, tmp_path):
        """ingest() saves the vectorstore to FAISS_INDEX_PATH and writes an empty
        history file so restore() finds consistent state."""
        index_path = str(tmp_path / "faiss_index")
        history_file = tmp_path / "history.json"
        fake_vectorstore = MagicMock()

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", index_path), \
             patch.object(state_module, "HISTORY_PATH", str(history_file)), \
             patch.object(ingestion_module, "is_readable", return_value=(True, "")), \
             patch.object(ingestion_module, "load_and_split", return_value=[MagicMock()]), \
             patch.object(ingestion_module, "create_vectorstore", return_value=fake_vectorstore), \
             patch.object(ingestion_module, "save_vectorstore") as mock_save, \
             patch.object(ingestion_module, "create_chain", return_value=MagicMock()):

            st = AppState()
            ingest([("a.pdf", b"pdf-a")], app_state=st)

        mock_save.assert_called_once_with(fake_vectorstore, index_path)
        assert json.loads(history_file.read_text(encoding="utf-8")) == []

    def test_ingest_raises_and_leaves_state_untouched_when_unreadable(self, tmp_path):
        """ingest() raises PDFNotReadableError naming the bad file and does not
        touch chain/loaded_files when a PDF is not readable."""
        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "faiss_index")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "is_readable", return_value=(False, "no readable text")), \
             patch.object(ingestion_module, "load_and_split") as mock_split, \
             patch.object(ingestion_module, "create_vectorstore") as mock_vs:

            st = AppState()
            with pytest.raises(PDFNotReadableError, match="bad.pdf"):
                ingest([("bad.pdf", b"scanned")], app_state=st)

        mock_split.assert_not_called()
        mock_vs.assert_not_called()
        assert st.chain is None
        assert st.loaded_files == []

    def test_ingest_validates_every_file_before_processing(self, tmp_path):
        """ingest() rejects the batch when any file is unreadable, even if the
        first one is fine."""
        readable_results = iter([(True, ""), (False, "no readable text")])

        with patch.object(ingestion_module, "FAISS_INDEX_PATH", str(tmp_path / "faiss_index")), \
             patch.object(state_module, "HISTORY_PATH", str(tmp_path / "history.json")), \
             patch.object(ingestion_module, "is_readable", side_effect=readable_results), \
             patch.object(ingestion_module, "load_and_split") as mock_split:

            st = AppState()
            with pytest.raises(PDFNotReadableError, match="bad.pdf"):
                ingest([("good.pdf", b"ok"), ("bad.pdf", b"scanned")], app_state=st)

        mock_split.assert_not_called()
