# DESIGN.md

## Requirement Summary

Currently `/api/ask` returns only the LLM's synthesized answer text, with no way
for the user to verify which part of the original document supports it. This
ticket adds a source-quote block appended after the answer, showing the page
it came from and a short excerpt (hit sentence ± 2 sentences on each side,
~5 sentences total) that supports the answer. Edge cases: if the hit sentence
is the first/last sentence on its page, the quote simply starts/ends there
without a missing side.

## Design

**Ingestion change:** Switch `PDFMinerLoader` from the default `mode="single"`
to `mode="page"`, so each PDF page becomes its own Document instead of the
whole PDF being collapsed into one Document before splitting. This means every
chunk produced afterward carries a page number in its metadata (previously no
chunk had any page information at all).

**Answer flow (per question), building on the existing retrieval/answer
generation which is unchanged:**

1. Retrieval and answer generation proceed as today: top-4 chunks are
   retrieved by similarity to the question and stuffed into the prompt; the
   LLM produces the answer text. No chunk selection happens at this stage
   today, and this design does not change that.
2. New post-processing step — **hit sentence identification**: split the text
   of all 4 retrieved chunks into individual sentences, pooled together (each
   sentence tagged with the page number of the chunk it came from). Compute
   similarity between the generated answer and every sentence in this pool;
   the single highest-scoring sentence is the "hit sentence," and its page
   becomes the citation's source page.
3. Build the quote block: take the hit sentence plus up to 2 sentences before
   and after it **within the same page**. If the hit sentence is the first
   sentence on the page, there is nothing before it to include; symmetrically
   for the last sentence on the page.
4. Append the quote block after the answer text, with a separator line noting
   the page number (chapter name is not included — see below).
5. **Scope boundary:** only a single citation (one page) is produced per
   answer, even though the 4 retrieved chunks may span multiple, non-adjacent
   pages. Multi-source/multi-page citations are out of scope for this
   iteration.
