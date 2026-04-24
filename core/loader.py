# core/loader.py
import tempfile
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFMinerLoader
from pdfminer.high_level import extract_text
from config import CHUNK_SIZE, CHUNK_OVERLAP

def load_and_split(uploaded_files):
    print(f"load_and_split called with {len(uploaded_files)} files")
    all_docs = []
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        loader = PDFMinerLoader(tmp_path)
        docs = loader.load()
        os.unlink(tmp_path)
        all_docs.extend(docs)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(all_docs)

def is_readable(uploaded_files):
    """
    Check if the PDF files contain readable text.
    Returns (bool, str) - (is_readable, message)
    """
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        
        text = extract_text(tmp_path, page_numbers=[0, 1, 2])
        os.unlink(tmp_path)
        
        readable_chars = sum(1 for c in text if c.isalpha())
        if readable_chars < 50:
            return False, f"'{uploaded_file.name}' does not contain readable text. It may be scanned or encrypted."

        uploaded_file.seek(0)
    
    return True, ""