# app.py
import streamlit as st
from ui.chat import init_session_state, render_chat
from ui.sidebar import render_sidebar

st.title("🍽️ PDF Eater")
st.caption("Upload your PDFs and ask anything about them.")

init_session_state()
render_sidebar()
render_chat()