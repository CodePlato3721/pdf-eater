# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Eater is a PDF Q&A application. Currently migrating from a Streamlit single-page app to a **React frontend + FastAPI backend**. Task tracking: [`.plato-kanban/TASKS.md`](.plato-kanban/TASKS.md).

## Running the Current App

```bash
# Install dependencies and create venv (first time or after pyproject.toml changes)
uv sync

# Set your OpenAI API key in a .env file
# OPENAI_API_KEY=your_key_here

# Run the Streamlit app
uv run streamlit run app.py
```

## Architecture

See [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md).

