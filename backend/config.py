CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MODEL_NAME = "gpt-3.5-turbo"
TOP_K = 4
FAISS_INDEX_PATH = "data/faiss_index"
HISTORY_PATH = "data/history.json"
# Sentences included before/after the hit sentence in a citation quote block.
CONTEXT_SENTENCES = 2
FRONTEND_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
