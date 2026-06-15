# CODER.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Rules

- **Never commit changes directly.** After making any code modifications, stop and wait for the user to review the diff before creating any git commit.
- **同时加载项目规则文件**：加载 `CODER.md` 时，必须同时读取 `CR.md` 和 `ARCHITECTURE.md`,``STANDARDS.md``。

## Commands

```bash
# Install dependencies (uses .venv in project root, Python 3.12)
pip install -r requirements.txt

# Run the Streamlit app
streamlit run app.py
```

The project has no lint or unit test configuration.

## Environment

Set `OPENAI_API_KEY` before running anything — used for OpenAI Embeddings and ChatOpenAI (gpt-3.5-turbo).

## Key files

| Path | Role |
|---|---|
| `app.py` | 入口：组装 Streamlit 页面，调用 ui 层 |
| `config.py` | 全局常量：CHUNK_SIZE、CHUNK_OVERLAP、MODEL_NAME、TOP_K |
| `core/loader.py` | PDF 读取（PDFMinerLoader）、切分（RecursiveCharacterTextSplitter）、可读性校验 |
| `core/embeddings.py` | 向量化（OpenAIEmbeddings）、向量库构建（DocArrayInMemorySearch） |
| `core/chain.py` | ConversationalRetrievalChain 构建，持有检索器和 ChatOpenAI |
| `ui/sidebar.py` | 文件上传触发逻辑、处理状态写入 session_state |
| `ui/chat.py` | session_state 初始化、对话渲染、问答调用 |
