# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Eater is a PDF Q&A application with a **React frontend + FastAPI backend**. The backend API lives in `backend/`; the React 18 + Vite frontend lives in `frontend/`.

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

```bash
cd frontend

# Install dependencies (first time or after package.json changes)
npm install

# Run the Vite dev server (http://localhost:5173)
npm run dev
```

## Running Backend Tests

```bash
cd backend
uv run pytest tests/unit
```

## Running Frontend Tests

```bash
cd frontend
npm test                          # unit tests (Vitest)
npx playwright install chromium   # one-time browser download for e2e
npm run test:e2e                  # e2e tests (Playwright)
```

## Architecture

See [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md).

