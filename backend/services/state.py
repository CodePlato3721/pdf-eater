import json
import logging
import os

from config import FAISS_INDEX_PATH, HISTORY_PATH
from core.embeddings import create_vectorstore, load_vectorstore, save_vectorstore
from core.chain import create_chain
from core.loader import is_readable, load_and_split

logger = logging.getLogger(__name__)


class PDFNotReadableError(Exception):
    """Raised when an uploaded PDF contains no readable text (e.g. scanned or encrypted)."""


class AppState:
    def __init__(self):
        self.chain = None
        self.chat_history: list = []
        self.loaded_files: list[str] = []

    def ingest(self, files: list[tuple[str, bytes]]) -> None:
        """
        Run the document ingestion pipeline for uploaded PDFs.

        Validates every file before any processing so a bad file rejects the
        whole batch, then loads/splits, builds the FAISS vectorstore, rebuilds
        the QA chain, and persists index + (reset) history so restore() works.

        Args:
            files: List of (filename, raw PDF bytes) pairs.

        Raises:
            PDFNotReadableError: If any PDF has no readable text.
        """
        for name, pdf_bytes in files:
            readable, reason = is_readable(pdf_bytes)
            if not readable:
                raise PDFNotReadableError(f"{name}: {reason}")

        docs = load_and_split([pdf_bytes for _, pdf_bytes in files])
        vectorstore = create_vectorstore(docs)
        save_vectorstore(vectorstore, FAISS_INDEX_PATH)
        self.chain = create_chain(vectorstore)
        self.loaded_files = [name for name, _ in files]
        self.chat_history = []
        self.save_history()

    def save_history(self) -> None:
        """Persist chat_history to HISTORY_PATH, creating the parent dir if needed."""
        parent_dir = os.path.dirname(HISTORY_PATH)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.chat_history, f, ensure_ascii=False)

    def restore(self) -> None:
        if os.path.isdir(FAISS_INDEX_PATH):
            try:
                vectorstore = load_vectorstore(FAISS_INDEX_PATH)
                self.chain = create_chain(vectorstore)
            except Exception as exc:
                logger.error("Failed to restore FAISS index: %s. Starting with empty state.", exc)
                self.chain = None

        if os.path.isfile(HISTORY_PATH):
            try:
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    self.chat_history = json.load(f)
            except Exception as exc:
                logger.error("Failed to restore chat history: %s", exc)
                self.chat_history = []


state = AppState()
