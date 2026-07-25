# BACKLOGS

Deferred opening questions from ticket design reviews. Use these as reference when creating new tickets.

## PD-04
- PM/Dev: Chapter-level citation ("Chapter 22") deferred — considered approach is regex-detecting chapter-heading patterns per page plus forward-filling a page→chapter mapping for pages without their own heading. Revisit as a follow-up ticket once page-only citation ships.

## PD-09
- Dev: "When does Josephine first appear?" still answers "I don't know" even though the book does contain "Josephine" (a rare alias — the character is called "Jo" almost everywhere else). Measured: chunks containing the literal string "Josephine" rank ~26th/27th out of ~880 under the FAISS similarity search for this query, far outside any reasonable TOP_K, so retrieval never surfaces them. Root cause is a retrieval-recall gap in pure embedding-similarity search for rare literal names/aliases, not a prompt issue (out of scope for PD-09's small fix). Proper fix likely needs hybrid retrieval (e.g. BM25 alongside FAISS) or alias-aware query expansion. Revisit as a follow-up ticket.
