# DESIGN.md

## Requirement Summary
When a user asks a question, before the question is embedded and used for vector retrieval, the system should first use HyDE (Hypothetical Document Embeddings): generate a hypothetical answer to the question, and embed that hypothetical answer instead of the raw question. Acceptance is confirmed by verifying the question-to-hypothetical-answer conversion actually happens in the ask flow.

## Design
The retriever used in the Q&A chain is replaced with a HyDE-based retriever.

Flow:
1. The chain condenses the user's question and chat history into a standalone question, as it already does today.
2. The new retriever takes that standalone question and makes one call to the existing LLM (the same LLM instance already used elsewhere in the chain) to generate a hypothetical answer to it.
3. The hypothetical answer is embedded, and that embedding is used to run the similarity search against the vector store, instead of embedding the standalone question directly.
4. The rest of the flow (stuffing retrieved chunks into the QA prompt, generating the final answer, updating chat history) is unchanged.

If the LLM call to generate the hypothetical answer fails, the `/api/ask` request fails with an error rather than silently falling back to embedding the raw question.
