import json
import logging
import os

from config import FAISS_INDEX_PATH, HISTORY_PATH
from core.embeddings import load_vectorstore
from core.chain import create_chain

logger = logging.getLogger(__name__)


class AppState:
    def __init__(self):
        self.chain = None
        self.chat_history: list = []
        self.loaded_files: list[str] = []

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
