# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Eater is a PDF Q&A application. The current codebase is a Streamlit single-page app. There is an **active migration plan** (see [`.plato-kanban/PLAN.md`](.plato-kanban/PLAN.md)) to split it into a **React frontend + FastAPI backend**.

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

## child agent

```
$env:CLAUDE_CONFIG_DIR = "$PWD\.plato-coder"
claude -p --dangerously-skip-permissions --output-format stream-json --append-system-prompt-file .\.plato-coder\CODER.md --session-id "9b7e4f2a-1c3d-4e5f-8a9b-0c1d2e3f4a5b" "请读取 .plato-kanban/TASKS.md，执行其中的 TASK-01"
```

唤起并询问
```
$env:CLAUDE_CONFIG_DIR = "$PWD\.plato-coder"
claude --resume "3d8f1a2b-4c5e-6f7a-8b9c-0d1e2f3a4b5c"
```