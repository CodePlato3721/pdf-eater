from services.state import AppState, state


class NoDocumentLoadedError(Exception):
    """Raised when a question is asked before any document has been ingested."""


def ask(question: str, app_state: AppState = state) -> str:
    """
    Answer a question via the QA chain using the current chat history.

    Appends the exchange to chat_history (persisted), and records the
    chain's generated retrieval query and source snippets as debug info.

    Args:
        question: The user's question.
        app_state: Session state to read/update; defaults to the app singleton.

    Returns:
        The chain's answer text.

    Raises:
        NoDocumentLoadedError: If no document has been ingested yet.
    """
    if app_state.chain is None:
        raise NoDocumentLoadedError("No document loaded. Upload a PDF first.")

    # History restored from JSON is a list of lists; the chain requires
    # (human, ai) tuples.
    history = [tuple(turn) for turn in app_state.chat_history]
    result = app_state.chain.invoke({"question": question, "chat_history": history})
    answer = result["answer"]

    app_state.chat_history.append((question, answer))
    app_state.save_history()
    app_state.last_query = result.get("generated_question", "")
    app_state.last_sources = [
        {"content": doc.page_content, "metadata": doc.metadata}
        for doc in result.get("source_documents", [])
    ]
    return answer
