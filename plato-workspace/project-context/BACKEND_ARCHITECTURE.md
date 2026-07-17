# Backend Architecture — RAG / Vector Search

Snapshot of `backend/`'s Q&A pipeline as of PD-04. Re-derive from source if
these files have since changed structurally.

## Stack

- Orchestration: **LangChain** (`ConversationalRetrievalChain`)
- Vector store: **FAISS** (`langchain_community.vectorstores.FAISS`), persisted at `data/faiss_index` (`FAISS_INDEX_PATH`, `backend/config.py`)
- Embeddings: `OpenAIEmbeddings()` (default model, no override)
- LLM: `ChatOpenAI(model="gpt-3.5-turbo", temperature=0)` (`MODEL_NAME`, `backend/config.py`)
- Retrieval: `search_type="similarity"`, `k=4` (`TOP_K`, `backend/config.py`)
- Chunking: `RecursiveCharacterTextSplitter`, `chunk_size=1000`, `chunk_overlap=150` (`CHUNK_SIZE`/`CHUNK_OVERLAP`, `backend/config.py`)

## Ingestion pipeline

`backend/services/ingestion.py`

- `ingest(files)`: validates every file is readable first (`is_readable`,
  `backend/core/loader.py`, rejects scanned/encrypted PDFs with
  `PDFNotReadableError`), then `load_and_split` → `create_vectorstore` →
  `save_vectorstore` → rebuilds `state.chain` → resets `state.chat_history`.
- `restore()`: on app startup, rebuilds `state.chain` from the persisted FAISS
  index at `FAISS_INDEX_PATH` if present, and reloads chat history.

`backend/core/loader.py`, `load_and_split()`:
- Each uploaded PDF is written to a temp file and loaded via
  `PDFMinerLoader(tmp_path)` using the **default `mode="single"`** — the
  entire PDF becomes **one Document**, so page boundaries are collapsed
  *before* splitting.
- That single Document is then split by `RecursiveCharacterTextSplitter`
  (character-count based, not sentence/page-aware).

**Known limitation (relevant to PD-04):** because of `mode="single"`, each
chunk's `metadata` only carries `source` (a temp file path, not the original
filename) and `total_pages` (whole-document count). **No chunk has a page
number, chapter, or section** — any "Chapter 22" text in an LLM answer is the
model reading/repeating it from the chunk's raw text, not something the
system extracted structurally. Adding real page/chapter citations requires
changing ingestion (e.g. per-page loading, or chapter detection) before this
metadata gap is closed.

## `/api/ask` request flow

`backend/main.py` → `POST /api/ask` (`AskRequest{question: str}`) → `backend/services/qa.py::ask()`:

1. Converts stored `state.chat_history` (list of `[question, answer]` pairs)
   into `(human, ai)` tuples.
2. Calls `chain.invoke({"question": question, "chat_history": history})`
   (chain built in `backend/core/chain.py::create_chain()`).
3. Inside `ConversationalRetrievalChain`:
   - Condenses `question` + `chat_history` into a standalone
     `generated_question` (LLM call, skipped/near-passthrough when history is
     empty).
   - Embeds the standalone question, runs FAISS similarity search (`k=4`).
   - Stuffs the 4 retrieved chunks into the QA prompt, calls the LLM, returns
     `{answer, source_documents, generated_question, ...}`.
4. `qa.ask()` appends `(question, answer)` to `state.chat_history` and
   persists it (`state.save_history()`, → `data/history.json`); stores
   `generated_question` in `state.last_query` and
   `[{content, metadata} for each source_document]` in `state.last_sources`
   (debug info only).
5. Returns just `answer: str` to the route, which responds
   `{"answer": answer}`.

**Source documents / chunk text are not part of the `/api/ask` response.**
They're only inspectable via `GET /api/debug` → `{"query": state.last_query,
"sources": state.last_sources}`, and only reflect the *most recent* question.

## State

`backend/services/state.py::AppState` — a process-lifetime singleton
(`state`), not per-session: `chain`, `chat_history` (persisted to
`HISTORY_PATH`), `loaded_files`, `last_query`, `last_sources`.

## Key files

| File | Role |
|---|---|
| `backend/config.py` | All tunables: chunk size/overlap, model, top-k, index/history paths |
| `backend/main.py` | FastAPI routes: `/api/status`, `/api/upload`, `/api/history`, `/api/ask`, `/api/debug` |
| `backend/core/loader.py` | PDF → Documents → chunks (`load_and_split`, `is_readable`) |
| `backend/core/embeddings.py` | FAISS create/save/load |
| `backend/core/chain.py` | Builds the `ConversationalRetrievalChain` |
| `backend/services/ingestion.py` | Upload pipeline + startup restore |
| `backend/services/qa.py` | `/api/ask` business logic |
| `backend/services/state.py` | In-memory + persisted app state |
