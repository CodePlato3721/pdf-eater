# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Eater is a PDF Q&A application, currently migrating to a **React frontend + FastAPI backend**. The backend API lives in `backend/`; the former Streamlit UI has been removed. The React frontend does not exist yet.

## Running the Current App

```bash
cd backend

# Install dependencies and create venv (first time or after pyproject.toml changes)
uv sync

# Set your OpenAI API key in a .env file
# OPENAI_API_KEY=your_key_here

# Run the FastAPI backend
uv run uvicorn main:app --reload
```

## Running Backend Tests

```bash
cd backend
uv run pytest tests/unit
```

## Architecture

See [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md).

