"""
Unit tests for backend/core modules.

Run from the backend/ directory:
    ../.venv/Scripts/python.exe -m pytest tests/unit/test_core.py -v
"""
import sys
import types

# ---------------------------------------------------------------------------
# Stub out heavy optional packages that may not be installed in the test env
# (e.g. faiss-cpu). We patch at the module level so that import succeeds.
# ---------------------------------------------------------------------------
# Provide a minimal faiss stub if the real package is absent
if "faiss" not in sys.modules:
    faiss_stub = types.ModuleType("faiss")
    sys.modules["faiss"] = faiss_stub

import pytest
from unittest.mock import MagicMock, patch, call


# ===========================================================================
# Tests for backend/core/loader.py
# ===========================================================================

class TestLoadAndSplit:
    """Tests for load_and_split()"""

    def _patch_fs(self):
        """Stub out tempfile/os so no real files are created."""
        import contextlib
        import unittest.mock as um

        @contextlib.contextmanager
        def _ctx():
            fake_tmp = MagicMock()
            fake_tmp.__enter__ = MagicMock(return_value=fake_tmp)
            fake_tmp.__exit__ = MagicMock(return_value=False)
            fake_tmp.name = "/tmp/fake_test.pdf"
            with um.patch("core.loader.tempfile.NamedTemporaryFile", return_value=fake_tmp), \
                 um.patch("core.loader.os.unlink"):
                yield

        return _ctx()

    def test_returns_split_documents(self):
        """load_and_split should call PDFMinerLoader for each bytes entry and
        return the result of RecursiveCharacterTextSplitter.split_documents."""
        from langchain_core.documents import Document

        fake_doc = Document(page_content="Hello world " * 100, metadata={})
        fake_split = [
            Document(page_content="Hello world " * 50, metadata={}),
            Document(page_content="Hello world " * 50, metadata={}),
        ]

        with self._patch_fs(), \
             patch("core.loader.PDFMinerLoader") as MockLoader, \
             patch("core.loader.RecursiveCharacterTextSplitter") as MockSplitter:

            mock_loader_instance = MagicMock()
            mock_loader_instance.load.return_value = [fake_doc]
            MockLoader.return_value = mock_loader_instance

            mock_splitter_instance = MagicMock()
            mock_splitter_instance.split_documents.return_value = fake_split
            MockSplitter.return_value = mock_splitter_instance

            from core import loader
            result = loader.load_and_split([b"%PDF fake bytes", b"%PDF more bytes"])

        # PDFMinerLoader should have been constructed twice (one per file)
        assert MockLoader.call_count == 2
        # split_documents should be called once with all collected docs
        mock_splitter_instance.split_documents.assert_called_once_with([fake_doc, fake_doc])
        assert result == fake_split

    def test_empty_list_returns_empty(self):
        """load_and_split with an empty list should return []."""
        with patch("core.loader.PDFMinerLoader"), \
             patch("core.loader.RecursiveCharacterTextSplitter") as MockSplitter:

            mock_splitter_instance = MagicMock()
            mock_splitter_instance.split_documents.return_value = []
            MockSplitter.return_value = mock_splitter_instance

            from core import loader
            result = loader.load_and_split([])

        mock_splitter_instance.split_documents.assert_called_once_with([])
        assert result == []


class TestIsReadable:
    """Tests for is_readable()"""

    def _patch_fs(self):
        """Return a context manager that stubs out tempfile/os calls in core.loader."""
        import contextlib
        import unittest.mock as um

        @contextlib.contextmanager
        def _ctx():
            fake_tmp = MagicMock()
            fake_tmp.__enter__ = MagicMock(return_value=fake_tmp)
            fake_tmp.__exit__ = MagicMock(return_value=False)
            fake_tmp.name = "/tmp/fake_test.pdf"
            with um.patch("core.loader.tempfile.NamedTemporaryFile", return_value=fake_tmp), \
                 um.patch("core.loader.os.unlink"):
                yield

        return _ctx()

    def test_readable_pdf_returns_true(self):
        """is_readable should return (True, '') for text-rich content."""
        readable_text = "a" * 200  # 200 alphabetic chars — well above threshold

        with self._patch_fs(), patch("core.loader.extract_text", return_value=readable_text):
            from core import loader
            ok, msg = loader.is_readable(b"%PDF fake")

        assert ok is True
        assert msg == ""

    def test_unreadable_pdf_returns_false(self):
        """is_readable should return (False, reason) when alphabetic char count < 50."""
        sparse_text = "a" * 10  # only 10 alphabetic chars — below threshold

        with self._patch_fs(), patch("core.loader.extract_text", return_value=sparse_text):
            from core import loader
            ok, msg = loader.is_readable(b"%PDF fake")

        assert ok is False
        assert len(msg) > 0

    def test_exact_threshold_unreadable(self):
        """49 alphabetic chars should be unreadable (threshold is < 50)."""
        text = "a" * 49

        with self._patch_fs(), patch("core.loader.extract_text", return_value=text):
            from core import loader
            ok, _ = loader.is_readable(b"%PDF fake")

        assert ok is False

    def test_exact_threshold_readable(self):
        """50 alphabetic chars should be readable."""
        text = "a" * 50

        with self._patch_fs(), patch("core.loader.extract_text", return_value=text):
            from core import loader
            ok, _ = loader.is_readable(b"%PDF fake")

        assert ok is True


# ===========================================================================
# Tests for backend/core/embeddings.py
# ===========================================================================

class TestCreateVectorstore:
    """Tests for create_vectorstore()"""

    def test_calls_faiss_from_documents(self):
        """create_vectorstore should call FAISS.from_documents with docs and embeddings."""
        from langchain_core.documents import Document

        fake_docs = [Document(page_content="chunk", metadata={})]
        fake_vectorstore = MagicMock()

        with patch("core.embeddings.OpenAIEmbeddings") as MockEmbeddings, \
             patch("core.embeddings.FAISS") as MockFAISS:

            mock_embeddings_instance = MagicMock()
            MockEmbeddings.return_value = mock_embeddings_instance
            MockFAISS.from_documents.return_value = fake_vectorstore

            from core import embeddings
            result = embeddings.create_vectorstore(fake_docs)

        MockEmbeddings.assert_called_once()
        MockFAISS.from_documents.assert_called_once_with(fake_docs, mock_embeddings_instance)
        assert result is fake_vectorstore


class TestSaveVectorstore:
    """Tests for save_vectorstore()"""

    def test_calls_save_local(self):
        """save_vectorstore should delegate to vectorstore.save_local(path)."""
        mock_vs = MagicMock()

        from core import embeddings
        embeddings.save_vectorstore(mock_vs, "data/faiss_index")

        mock_vs.save_local.assert_called_once_with("data/faiss_index")

    def test_save_local_path_passed_correctly(self):
        """save_vectorstore should pass the exact path string through."""
        mock_vs = MagicMock()
        custom_path = "/tmp/my_index"

        from core import embeddings
        embeddings.save_vectorstore(mock_vs, custom_path)

        mock_vs.save_local.assert_called_once_with(custom_path)


class TestLoadVectorstore:
    """Tests for load_vectorstore()"""

    def test_calls_faiss_load_local(self):
        """load_vectorstore should call FAISS.load_local with path, embeddings, and
        allow_dangerous_deserialization=True."""
        fake_vectorstore = MagicMock()

        with patch("core.embeddings.OpenAIEmbeddings") as MockEmbeddings, \
             patch("core.embeddings.FAISS") as MockFAISS:

            mock_embeddings_instance = MagicMock()
            MockEmbeddings.return_value = mock_embeddings_instance
            MockFAISS.load_local.return_value = fake_vectorstore

            from core import embeddings
            result = embeddings.load_vectorstore("data/faiss_index")

        MockFAISS.load_local.assert_called_once_with(
            "data/faiss_index",
            mock_embeddings_instance,
            allow_dangerous_deserialization=True,
        )
        assert result is fake_vectorstore

    def test_returns_vectorstore(self):
        """load_vectorstore should return whatever FAISS.load_local returns."""
        sentinel = object()

        with patch("core.embeddings.OpenAIEmbeddings"), \
             patch("core.embeddings.FAISS") as MockFAISS:

            MockFAISS.load_local.return_value = sentinel

            from core import embeddings
            result = embeddings.load_vectorstore("some/path")

        assert result is sentinel
