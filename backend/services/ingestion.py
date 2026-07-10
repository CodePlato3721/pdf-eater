import logging
import os

from config import FAISS_INDEX_PATH
from core.chain import create_chain
from core.embeddings import create_vectorstore, load_vectorstore, save_vectorstore
from core.loader import is_readable, load_and_split
from services.state import AppState, state

logger = logging.getLogger(__name__)


class PDFNotReadableError(Exception):
    """Raised when an uploaded PDF contains no readable text (e.g. scanned or encrypted)."""


def ingest(files: list[tuple[str, bytes]], app_state: AppState = state) -> None:
    """
    Run the document ingestion pipeline for uploaded PDFs.

    Validates every file before any processing so a bad file rejects the
    whole batch, then loads/splits, builds the FAISS vectorstore, rebuilds
    the QA chain, and persists index + (reset) history so restore() works.

    Args:
        files: List of (filename, raw PDF bytes) pairs.
        app_state: Session state to update; defaults to the app singleton.

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
    app_state.chain = create_chain(vectorstore)
    app_state.loaded_files = [name for name, _ in files]
    app_state.chat_history = []
    app_state.save_history()


def restore(app_state: AppState = state) -> None:
    """Rebuild the QA chain from the persisted FAISS index and reload history."""
    if os.path.isdir(FAISS_INDEX_PATH):
        try:
            vectorstore = load_vectorstore(FAISS_INDEX_PATH)
            app_state.chain = create_chain(vectorstore)
        except Exception as exc:
            logger.error("Failed to restore FAISS index: %s. Starting with empty state.", exc)
            app_state.chain = None

    app_state.load_history()
