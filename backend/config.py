CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MODEL_NAME = "gpt-3.5-turbo"
TOP_K = 4
FAISS_INDEX_PATH = "data/faiss_index"
HISTORY_PATH = "data/history.json"
UPLOADED_FILES_PATH = "data/uploaded_files.json"
# Sentences included before/after the hit sentence in a citation quote block.
CONTEXT_SENTENCES = 2
# Minimum cosine similarity a hit sentence must have with the answer to be
# cited as supporting evidence; below this, no chunk is treated as relevant.
# PD-09: 0.4 was rejecting plenty of correct, on-topic, but shorter/paraphrased
# answers (bag-of-words overlap with the source sentence is a weak proxy for
# correctness), scoring not far above known hallucinated-answer cases (e.g.
# ~0.09-0.12 for the PD-07/PD-08 Bhaer/Hagar mismatch). 0.2 keeps a margin
# above those known mismatches while accepting more legitimate short answers;
# it's a compromise, not a full fix — a very terse answer (e.g. "...at the
# age of thirteen.", ~0.19) can still narrowly fall under it.
MIN_CITATION_SIMILARITY = 0.2
FRONTEND_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
