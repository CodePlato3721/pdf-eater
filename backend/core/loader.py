import tempfile
import os
from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pdfminer.high_level import extract_text
from config import CHUNK_SIZE, CHUNK_OVERLAP


def load_and_split(pdf_bytes_list: list) -> list:
    """
    Load and split PDF files from raw bytes.

    Args:
        pdf_bytes_list: List of raw PDF bytes, one per file.

    Returns:
        List of Document objects after splitting.
    """
    all_docs = []
    for pdf_bytes in pdf_bytes_list:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        try:
            loader = PDFMinerLoader(tmp_path, mode="page")
            docs = loader.load()
        finally:
            os.unlink(tmp_path)
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(all_docs)


def is_readable(pdf_bytes: bytes) -> tuple:
    """
    Check if a single PDF file (given as raw bytes) contains readable text.

    Args:
        pdf_bytes: Raw bytes of a single PDF file.

    Returns:
        (bool, str) — (True, "") if readable, (False, reason) otherwise.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        text = extract_text(tmp_path, page_numbers=[0, 1, 2])
    finally:
        os.unlink(tmp_path)

    readable_chars = sum(1 for c in text if c.isalpha())
    if readable_chars < 50:
        return False, "The PDF does not contain readable text. It may be scanned or encrypted."
    return True, ""
