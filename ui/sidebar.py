# ui/sidebar.py
import streamlit as st
from core.loader import load_and_split
from core.embeddings import create_vectorstore
from core.chain import create_chain
from core.loader import load_and_split, is_readable

def render_sidebar():
    """
    Render the sidebar with file uploader and debug info.
    """
    with st.sidebar:
        st.header("Upload Documents")

        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type="pdf",
            accept_multiple_files=True
        )

        # Auto-load when files are uploaded
        if uploaded_files:
            current_names = [f.name for f in uploaded_files]
            print(f"current_names: {current_names}")
            print(f"loaded_files: {st.session_state.get('loaded_files', [])}")
            print(f"equal: {current_names == st.session_state.get('loaded_files', [])}")
            if current_names != st.session_state.get("loaded_files", []):
                with st.spinner("Processing documents..."):
                    readable, message = is_readable(uploaded_files)
                    if not readable:
                        st.error(message)
                    else:
                        docs = load_and_split(uploaded_files)
                        vectorstore = create_vectorstore(docs)
                        st.session_state.qa = create_chain(vectorstore)
                        print(f"qa set: {st.session_state.qa is not None}")
                        st.session_state.chat_history = []
                        st.session_state.loaded_files = current_names
                        st.success(f"Loaded {len(uploaded_files)} file(s)")

        if st.button("Clear History"):
            st.session_state.chat_history = []

        # Debug info
        if st.session_state.get("last_query"):
            st.divider()
            st.subheader("Last DB Query")
            st.write(st.session_state.last_query)

        if st.session_state.get("last_sources"):
            st.divider()
            st.subheader("Retrieved Sources")
            for i, doc in enumerate(st.session_state.last_sources):
                page = doc.metadata.get('page', None)
                page_str = str(page + 1) if page is not None else '?'
                with st.expander(f"Source {i+1} - Page {page_str}"):
                    st.write(doc.page_content[:300] + "...")