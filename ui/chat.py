# ui/chat.py
import streamlit as st

def init_session_state():
    """
    Initialize session state variables.
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "qa" not in st.session_state:
        st.session_state.qa = None
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    if "loaded_files" not in st.session_state:
        st.session_state.loaded_files = []

def render_chat():
    print(f"render_chat called, qa is None: {st.session_state.qa is None}")
    print(f"chat_history length: {len(st.session_state.chat_history)}")
    """
    Render the chat interface.
    """
    # Display chat history
    for human_msg, ai_msg in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(human_msg)
        with st.chat_message("assistant"):
            st.write(ai_msg)

    # Chat input
    if question := st.chat_input("Ask a question about your PDF..."):
        if st.session_state.qa is None:
            st.warning("Please upload a PDF file first.")
            return

        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.qa.invoke({
                    "question": question,
                    "chat_history": st.session_state.chat_history
                })
                answer = result["answer"]
                st.write(answer)

        st.session_state.chat_history.append((question, answer))
        st.session_state.last_query = result.get("generated_question", "")
        st.session_state.last_sources = result.get("source_documents", [])
        st.rerun()