# DESIGN.md

## Requirement

**Original requirement:** Build the React 18 frontend for pdf-eater (step 2 of the frontend/backend split). The FastAPI backend already exists in `backend/`; the old Streamlit UI has been deleted (its layout is recoverable from git history).

**Refined requirement points:**
- Two-pane layout:
  - **Left panel**: list of already-uploaded PDFs.
  - **Right panel**: chat window. PDFs are uploaded as attachments from the chat input area; after upload, the user asks questions in the chat and answers appear in the chat window (e.g., upload *Little Women* and ask where a character first appears — the app finds the passage and shows it in chat).
- The frontend is not strictly bound to the current backend API — the backend may be modified as needed to fit the frontend requirements (e.g., CORS support, PDF list endpoint shape).
- Standard states to handle: upload in progress, answer in progress ("thinking"), upload/ask failure messages, no-document-loaded case.

**PM confirmation:** Not needed.

## External Dependencies

None. The backend is in this same repository and can be modified within this ticket if needed; no waiting on DBAs, other engineers, or external APIs.

## External Dependency Strategy

Not applicable — there are no unsatisfied external dependencies, work can start immediately.

## Design

- **Stack:** React 18 + Vite, in a new `frontend/` folder. Plain `fetch` calls to the FastAPI backend (no extra HTTP client).
- **Layout:** modeled on the old Streamlit UI — left sidebar + main chat area:
  - Left sidebar shows the list of uploaded PDFs (from `/api/status`).
  - Right chat area shows the conversation history and a chat input with a PDF attachment button; attaching PDFs uploads them via `/api/upload`, questions go through `/api/ask`, history via `/api/history`.
- **Flow:** user attaches PDF(s) in the chat input → upload → left panel refreshes with the file list → user types a question → answer is displayed in the chat window; a clear-history action resets the conversation.
- **Backend adjustments:** allowed where needed — at minimum CORS for the Vite dev server; other endpoint tweaks only if the frontend requires them.
- **Tests:** unit tests in `frontend/tests/unit`, e2e tests in `frontend/tests/e2e` (per status.json).
