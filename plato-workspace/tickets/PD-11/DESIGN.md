# DESIGN.md

## Requirement Summary

After a service restart, the left-hand document list currently comes back empty even if PDFs were previously uploaded, unlike chat history, which already survives a restart. Users expect the document list to behave the same way as chat history: show previously uploaded filenames after a restart, and show an empty (not erroring) list when nothing was ever uploaded.

## Design

Persist the uploaded-file list to disk the same way chat history is already persisted, and restore it on startup the same way chat history is already restored:

- On ingest, after the file list is set in memory, also write it out to a new JSON file at `backend/data/uploaded_files.json` (separate from the FAISS index and the history file), fully replacing its previous contents — matching the existing replace (not append) semantics of the in-memory file list.
- On startup, after attempting to restore the FAISS index, read that JSON file back into memory:
  - If the file doesn't exist (nothing was ever uploaded), the file list stays empty — no error, no file created just to satisfy the read.
  - If the FAISS index itself fails to load/restore, the file list is cleared rather than shown, so the displayed list never claims files are available when the underlying index isn't actually usable.
- Clearing chat history (`DELETE /api/history`) is left untouched and does not affect the persisted file list — that stays out of scope for this change.
