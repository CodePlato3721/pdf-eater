# PDF Eater 前后端分离 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将现有 Streamlit 单体应用拆分为 React (Vite) 前端 + FastAPI 后端，支持 FAISS 持久化和 SSE 流式回答。

**Architecture:** FastAPI 后端在 `backend/` 目录下，暴露 4 个 API 端点（upload、status、chat/stream、history）；React 前端在 `frontend/` 目录下，通过 Vite proxy 访问后端，使用 `fetch` + `ReadableStream` 实现 SSE 流式渲染；全局单例 `state.py` 持有 chain、chat_history 和 loaded_files，启动时自动从磁盘恢复。

**Tech Stack:** FastAPI、uvicorn、LangChain（langchain-classic）、langchain-openai、faiss-cpu、pdfminer.six、pytest、httpx（后端）；Vite、React 18、Tailwind CSS（前端）

---

## 文件结构一览

```
backend/
├── main.py                  # 创建
├── config.py                # 创建（从根目录 config.py 迁移）
├── state.py                 # 创建
├── routers/
│   ├── __init__.py          # 创建（空）
│   ├── upload.py            # 创建
│   └── chat.py              # 创建
├── core/
│   ├── __init__.py          # 创建（空）
│   ├── loader.py            # 创建（改造：接收 file path list，不依赖 Streamlit）
│   ├── embeddings.py        # 创建（改造：FAISS 替换 DocArrayInMemorySearch）
│   └── chain.py             # 创建（改造：LLM 加 streaming=True）
├── requirements.txt         # 创建
└── data/                    # 运行时自动生成

tests/
├── __init__.py              # 创建（空）
├── test_core.py             # 创建
├── test_state.py            # 创建
├── test_upload.py           # 创建
└── test_chat.py             # 创建

frontend/                    # npm create vite 生成后修改
├── vite.config.js           # 修改（加 proxy）
├── tailwind.config.js       # 创建
├── postcss.config.js        # 创建
└── src/
    ├── index.css            # 修改（加 Tailwind directives）
    ├── main.jsx             # 修改（清理 boilerplate）
    ├── App.jsx              # 创建（顶层布局）
    ├── api.js               # 创建
    ├── hooks/
    │   ├── useUpload.js     # 创建
    │   └── useChat.js       # 创建
    └── components/
        ├── Sidebar.jsx      # 创建
        ├── ChatPane.jsx     # 创建
        ├── MessageBubble.jsx# 创建
        └── SourcesPanel.jsx # 创建
```

---

## Task 1: 后端脚手架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/main.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/core/__init__.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p backend/routers backend/core backend/data tests
touch backend/__init__.py backend/routers/__init__.py backend/core/__init__.py tests/__init__.py
```

- [ ] **Step 2: 创建 `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
langchain==0.3.0
langchain-openai==0.2.0
langchain-community==0.3.0
langchain-text-splitters==0.3.0
langchain-classic==0.0.1
faiss-cpu==1.8.0
pdfminer.six==20231228
python-dotenv==1.0.1
pytest==8.3.2
pytest-asyncio==0.23.8
httpx==0.27.2
```

> 注意：`langchain-classic` 提供 `ConversationalRetrievalChain`（现有代码依赖它）。若安装失败，改用 `from langchain.chains import ConversationalRetrievalChain`（旧版 langchain）。

- [ ] **Step 3: 安装依赖**

在 `backend/` 目录下创建并激活虚拟环境，然后安装：

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 4: 创建 `backend/config.py`**

```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MODEL_NAME = "gpt-3.5-turbo"
TOP_K = 4

FAISS_PATH = "data/faiss_index"
HISTORY_PATH = "data/history.json"
```

- [ ] **Step 5: 创建 `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, chat

app = FastAPI(title="PDF Eater API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
```

- [ ] **Step 6: 验证后端能启动**

```bash
cd backend
uvicorn main:app --reload --port 8000
```

预期输出中有 `Application startup complete.`（路由此时未完成，正常报 import error——下一步会修复）。先确认 FastAPI 本身能 import，然后 Ctrl+C 停止。

- [ ] **Step 7: Commit**

```bash
git add backend/ tests/
git commit -m "feat: backend scaffold - FastAPI app, config, directory structure"
```

---

## Task 2: 后端 core 层

**Files:**
- Create: `backend/core/loader.py`
- Create: `backend/core/embeddings.py`
- Create: `backend/core/chain.py`
- Create: `tests/test_core.py`

> **关键变更：** `loader.py` 接口从 Streamlit UploadFile 列表改为文件路径列表；`embeddings.py` 使用 FAISS；`chain.py` 的 LLM 加 `streaming=True`。

- [ ] **Step 1: 创建 `backend/core/loader.py`**

```python
import os
from langchain_community.document_loaders import PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pdfminer.high_level import extract_text
from config import CHUNK_SIZE, CHUNK_OVERLAP


def load_and_split(file_paths: list[str]) -> list:
    all_docs = []
    for path in file_paths:
        loader = PDFMinerLoader(path)
        all_docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(all_docs)


def is_readable(file_path: str) -> tuple[bool, str]:
    text = extract_text(file_path, page_numbers=[0, 1, 2])
    readable_chars = sum(1 for c in text if c.isalpha())
    if readable_chars < 50:
        return False, "文件不含可读文字（可能是扫描件或加密文件）"
    return True, ""
```

- [ ] **Step 2: 创建 `backend/core/embeddings.py`**

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


def create_vectorstore(docs):
    embeddings = OpenAIEmbeddings()
    return FAISS.from_documents(docs, embeddings)


def save_vectorstore(vectorstore, path: str):
    vectorstore.save_local(path)


def load_vectorstore(path: str):
    embeddings = OpenAIEmbeddings()
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
```

- [ ] **Step 3: 创建 `backend/core/chain.py`**

```python
from langchain_openai import ChatOpenAI
from langchain_classic.chains import ConversationalRetrievalChain
from config import MODEL_NAME, TOP_K


def create_chain(vectorstore):
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0, streaming=True)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        return_generated_question=True,
    )
```

- [ ] **Step 4: 写 `tests/test_core.py` 的失败测试**

```python
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# 把 backend/ 加入 sys.path，使 import 生效
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.loader import is_readable, load_and_split


def _make_tmp_pdf(content: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(content)
    tmp.close()
    return tmp.name


def test_is_readable_rejects_empty():
    path = _make_tmp_pdf(b"%PDF-1.4\n%%EOF")
    try:
        ok, msg = is_readable(path)
        assert not ok
        assert "可读文字" in msg
    finally:
        os.unlink(path)


def test_load_and_split_calls_loader():
    fake_docs = [MagicMock()]
    fake_chunks = [MagicMock()]
    with patch("core.loader.PDFMinerLoader") as MockLoader, \
         patch("core.loader.RecursiveCharacterTextSplitter") as MockSplitter:
        MockLoader.return_value.load.return_value = fake_docs
        MockSplitter.return_value.split_documents.return_value = fake_chunks

        result = load_and_split(["/fake/path.pdf"])

        MockLoader.assert_called_once_with("/fake/path.pdf")
        assert result == fake_chunks
```

- [ ] **Step 5: 运行测试，确认失败（因为依赖还没有 import 路径问题）**

```bash
cd backend && pytest ../tests/test_core.py -v
```

预期：如果路径配置正确，`test_load_and_split_calls_loader` 应该 PASS（因为全部 mock），`test_is_readable_rejects_empty` 取决于 pdfminer 是否能处理最小 PDF，可能 PASS 或报 parse error。任何 ImportError 说明 `sys.path` 设置需要调整——检查 `backend/` 目录是否在 `sys.path` 里。

- [ ] **Step 6: Commit**

```bash
git add backend/core/ tests/test_core.py
git commit -m "feat: backend core layer - loader, embeddings (FAISS), chain with streaming"
```

---

## Task 3: 后端 state 单例

**Files:**
- Create: `backend/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: 写 `tests/test_state.py` 的失败测试**

```python
import os
import sys
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_app_state_starts_empty_when_no_data(tmp_path):
    with patch("state.FAISS_PATH", str(tmp_path / "faiss")), \
         patch("state.HISTORY_PATH", str(tmp_path / "history.json")):
        import importlib
        import state as s
        importlib.reload(s)
        fresh = s.AppState()
        assert fresh.chain is None
        assert fresh.chat_history == []
        assert fresh.loaded_files == []


def test_save_and_reload_history(tmp_path):
    history_path = str(tmp_path / "history.json")
    with patch("state.FAISS_PATH", str(tmp_path / "faiss")), \
         patch("state.HISTORY_PATH", history_path):
        import importlib
        import state as s
        importlib.reload(s)

        st = s.AppState()
        st.chat_history = [("q1", "a1"), ("q2", "a2")]
        st.loaded_files = ["doc.pdf"]
        st.save_history()

        data = json.loads(open(history_path).read())
        assert data["history"] == [["q1", "a1"], ["q2", "a2"]]
        assert data["files"] == ["doc.pdf"]


def test_clear_history(tmp_path):
    history_path = str(tmp_path / "history.json")
    with patch("state.FAISS_PATH", str(tmp_path / "faiss")), \
         patch("state.HISTORY_PATH", history_path):
        import importlib
        import state as s
        importlib.reload(s)

        st = s.AppState()
        st.chat_history = [("q", "a")]
        st.clear_history()
        assert st.chat_history == []
```

- [ ] **Step 2: 运行确认测试失败（state.py 不存在）**

```bash
cd backend && pytest ../tests/test_state.py -v
```

预期：`ModuleNotFoundError: No module named 'state'`

- [ ] **Step 3: 创建 `backend/state.py`**

```python
import json
import os
from pathlib import Path

from config import FAISS_PATH, HISTORY_PATH


class AppState:
    def __init__(self):
        self.chain = None
        self.chat_history: list[tuple[str, str]] = []
        self.loaded_files: list[str] = []
        self._try_load()

    def _try_load(self):
        if Path(FAISS_PATH).exists():
            try:
                from core.embeddings import load_vectorstore
                from core.chain import create_chain
                vs = load_vectorstore(FAISS_PATH)
                self.chain = create_chain(vs)
            except Exception as e:
                print(f"[state] Failed to load vectorstore: {e}")

        if Path(HISTORY_PATH).exists():
            try:
                with open(HISTORY_PATH) as f:
                    data = json.load(f)
                self.chat_history = [tuple(item) for item in data.get("history", [])]
                self.loaded_files = data.get("files", [])
            except Exception as e:
                print(f"[state] Failed to load history: {e}")

    def save_history(self):
        Path("data").mkdir(exist_ok=True)
        with open(HISTORY_PATH, "w") as f:
            json.dump({"history": self.chat_history, "files": self.loaded_files}, f)

    def clear_history(self):
        self.chat_history = []
        self.save_history()


app_state = AppState()
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd backend && pytest ../tests/test_state.py -v
```

预期：3 个测试全部 PASS。

- [ ] **Step 5: Commit**

```bash
git add backend/state.py tests/test_state.py
git commit -m "feat: backend state singleton with FAISS and history persistence"
```

---

## Task 4: 上传路由（POST /api/upload + GET /api/status）

**Files:**
- Create: `backend/routers/upload.py`
- Create: `tests/test_upload.py`

- [ ] **Step 1: 写 `tests/test_upload.py` 的失败测试**

```python
import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@pytest.fixture
def client():
    with patch("state.AppState._try_load"):  # 防止启动时尝试加载磁盘数据
        from main import app
        return TestClient(app)


def test_status_no_files(client):
    with patch("routers.upload.app_state") as mock_state:
        mock_state.chain = None
        mock_state.loaded_files = []
        resp = client.get("/api/status")
        assert resp.status_code == 200
        assert resp.json() == {"loaded": False, "files": []}


def test_upload_non_pdf_rejected(client):
    resp = client.post(
        "/api/upload",
        files=[("files", ("test.txt", b"hello", "text/plain"))],
    )
    assert resp.status_code == 400
    assert "PDF" in resp.json()["detail"]


def test_upload_unreadable_pdf_rejected(client):
    with patch("routers.upload.is_readable", return_value=(False, "文件不含可读文字")):
        resp = client.post(
            "/api/upload",
            files=[("files", ("test.pdf", b"%PDF-1.4\n%%EOF", "application/pdf"))],
        )
    assert resp.status_code == 400
    assert "可读文字" in resp.json()["detail"]


def test_upload_success(client, tmp_path):
    fake_chunks = [MagicMock()]
    fake_vs = MagicMock()
    fake_chain = MagicMock()

    with patch("routers.upload.is_readable", return_value=(True, "")), \
         patch("routers.upload.load_and_split", return_value=fake_chunks), \
         patch("routers.upload.create_vectorstore", return_value=fake_vs), \
         patch("routers.upload.save_vectorstore"), \
         patch("routers.upload.create_chain", return_value=fake_chain), \
         patch("routers.upload.app_state") as mock_state:

        mock_state.save_history = MagicMock()
        resp = client.post(
            "/api/upload",
            files=[("files", ("doc.pdf", b"%PDF-1.4\n%%EOF", "application/pdf"))],
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    assert "doc.pdf" in resp.json()["files"]
```

- [ ] **Step 2: 运行确认失败**

```bash
cd backend && pytest ../tests/test_upload.py -v
```

预期：`ImportError` 或 `404`（路由未创建）。

- [ ] **Step 3: 创建 `backend/routers/upload.py`**

```python
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from config import FAISS_PATH
from core.chain import create_chain
from core.embeddings import create_vectorstore, save_vectorstore
from core.loader import is_readable, load_and_split
from state import app_state

router = APIRouter()


@router.post("/upload")
async def upload_pdfs(files: list[UploadFile] = File(...)):
    for f in files:
        if f.content_type != "application/pdf":
            raise HTTPException(400, detail=f"'{f.filename}' 不是 PDF 文件")

    tmp_paths: list[tuple[str, str]] = []
    try:
        for f in files:
            content = await f.read()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(content)
            tmp.close()
            tmp_paths.append((f.filename, tmp.name))

        for filename, path in tmp_paths:
            ok, msg = is_readable(path)
            if not ok:
                raise HTTPException(400, detail=f"'{filename}': {msg}")

        paths_only = [p for _, p in tmp_paths]
        chunks = load_and_split(paths_only)

        Path("data").mkdir(exist_ok=True)
        vectorstore = create_vectorstore(chunks)
        save_vectorstore(vectorstore, FAISS_PATH)

        app_state.chain = create_chain(vectorstore)
        app_state.chat_history = []
        app_state.loaded_files = [name for name, _ in tmp_paths]
        app_state.save_history()

        return {"status": "ok", "files": app_state.loaded_files}

    finally:
        for _, path in tmp_paths:
            try:
                os.unlink(path)
            except OSError:
                pass


@router.get("/status")
async def get_status():
    return {
        "loaded": app_state.chain is not None,
        "files": app_state.loaded_files,
    }
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd backend && pytest ../tests/test_upload.py -v
```

预期：4 个测试全部 PASS。

- [ ] **Step 5: Commit**

```bash
git add backend/routers/upload.py tests/test_upload.py
git commit -m "feat: upload router - POST /api/upload, GET /api/status"
```

---

## Task 5: 聊天路由（POST /api/chat/stream + DELETE /api/history）

**Files:**
- Create: `backend/routers/chat.py`
- Create: `tests/test_chat.py`

- [ ] **Step 1: 写 `tests/test_chat.py` 的失败测试**

```python
import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@pytest.fixture
def client():
    with patch("state.AppState._try_load"):
        from main import app
        return TestClient(app)


def test_chat_stream_no_docs_returns_400(client):
    with patch("routers.chat.app_state") as mock_state:
        mock_state.chain = None
        resp = client.post("/api/chat/stream", json={"question": "hello"})
    assert resp.status_code == 400
    assert "文档" in resp.json()["detail"]


def test_delete_history_clears_state(client):
    with patch("routers.chat.app_state") as mock_state:
        mock_state.clear_history = MagicMock()
        resp = client.delete("/api/history")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    mock_state.clear_history.assert_called_once()
```

> 注意：完整的 SSE 流测试需要真实的 OpenAI API key，此处只测 HTTP 层的守门逻辑。

- [ ] **Step 2: 运行确认失败**

```bash
cd backend && pytest ../tests/test_chat.py -v
```

预期：`ImportError` 或 `404`。

- [ ] **Step 3: 创建 `backend/routers/chat.py`**

```python
import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from pydantic import BaseModel

from state import app_state

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    if app_state.chain is None:
        raise HTTPException(400, detail="未加载任何文档，请先上传 PDF")

    async def event_generator():
        callback = AsyncIteratorCallbackHandler()

        async def run_chain():
            return await app_state.chain.acall(
                {
                    "question": body.question,
                    "chat_history": app_state.chat_history,
                },
                callbacks=[callback],
            )

        task = asyncio.create_task(run_chain())

        try:
            async for token in callback.aiter():
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            return

        try:
            result = await task
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            return

        app_state.chat_history.append((body.question, result["answer"]))
        app_state.save_history()

        sources = [
            {
                "page": doc.metadata.get("page", 0) + 1,
                "text": doc.page_content[:300],
            }
            for doc in result.get("source_documents", [])
        ]
        yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.delete("/history")
async def delete_history():
    app_state.clear_history()
    return {"status": "ok"}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd backend && pytest ../tests/test_chat.py -v
```

预期：2 个测试 PASS。

- [ ] **Step 5: 运行全部后端测试**

```bash
cd backend && pytest ../tests/ -v
```

预期：所有测试 PASS。

- [ ] **Step 6: 手动启动后端验证 API 文档可访问**

```bash
cd backend && uvicorn main:app --reload --port 8000
```

浏览器打开 `http://localhost:8000/docs`，应看到 4 个端点：`/api/upload`、`/api/status`、`/api/chat/stream`、`/api/history`。

- [ ] **Step 7: Commit**

```bash
git add backend/routers/chat.py tests/test_chat.py
git commit -m "feat: chat router - POST /api/chat/stream (SSE), DELETE /api/history"
```

---

## Task 6: 前端脚手架（Vite + React + Tailwind）

**Files:**
- Create: `frontend/` (通过 npm create vite)
- Modify: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Modify: `frontend/src/index.css`
- Modify: `frontend/src/main.jsx`

- [ ] **Step 1: 创建 Vite + React 项目**

在 `pdf-eater/` 根目录执行：

```bash
npm create vite@latest frontend -- --template react
```

出现交互提示时选择 `React` → `JavaScript`（不选 TypeScript）。

- [ ] **Step 2: 安装依赖 + Tailwind**

```bash
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 3: 修改 `frontend/tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 4: 修改 `frontend/src/index.css`（替换全部内容）**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: 修改 `frontend/vite.config.js`（加 proxy）**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 6: 修改 `frontend/src/main.jsx`（清理 boilerplate）**

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 7: 创建临时 `frontend/src/App.jsx`（用于验证启动）**

```jsx
export default function App() {
  return <div className="p-4 text-xl font-bold">PDF Eater</div>
}
```

- [ ] **Step 8: 验证前端能启动**

```bash
cd frontend && npm run dev
```

浏览器打开 `http://localhost:5173`，应看到 "PDF Eater" 字样，并且 Tailwind 样式生效（字体加粗）。

- [ ] **Step 9: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold - Vite, React, Tailwind, API proxy"
```

---

## Task 7: api.js — 统一 fetch 出口

**Files:**
- Create: `frontend/src/api.js`

- [ ] **Step 1: 创建 `frontend/src/api.js`**

```javascript
export async function getStatus() {
  const res = await fetch('/api/status')
  if (!res.ok) throw new Error('Failed to fetch status')
  return res.json()
}

export async function uploadFiles(files) {
  const form = new FormData()
  for (const file of files) form.append('files', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail || 'Upload failed')
  }
  return res.json()
}

export async function clearHistory() {
  const res = await fetch('/api/history', { method: 'DELETE' })
  if (!res.ok) throw new Error('Failed to clear history')
  return res.json()
}

export async function* streamChat(question) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Chat failed' }))
    throw new Error(err.detail || 'Chat failed')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6))
      }
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: frontend api.js - fetch wrappers for all backend endpoints"
```

---

## Task 8: useUpload hook + Sidebar 组件

**Files:**
- Create: `frontend/src/hooks/useUpload.js`
- Create: `frontend/src/components/Sidebar.jsx`

- [ ] **Step 1: 创建 `frontend/src/hooks/useUpload.js`**

```javascript
import { useState, useCallback } from 'react'
import { uploadFiles } from '../api.js'

export function useUpload(onSuccess) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState(null)

  const upload = useCallback(async (files) => {
    setIsUploading(true)
    setError(null)
    try {
      const result = await uploadFiles(files)
      onSuccess(result.files)
    } catch (e) {
      setError(e.message)
    } finally {
      setIsUploading(false)
    }
  }, [onSuccess])

  return { upload, isUploading, error }
}
```

- [ ] **Step 2: 创建 `frontend/src/components/Sidebar.jsx`**

```jsx
import { useRef } from 'react'
import { useUpload } from '../hooks/useUpload.js'
import { clearHistory } from '../api.js'

export default function Sidebar({ loadedFiles, onFilesLoaded, onHistoryCleared }) {
  const inputRef = useRef(null)
  const { upload, isUploading, error } = useUpload(onFilesLoaded)

  function handleFileChange(e) {
    const files = Array.from(e.target.files)
    if (files.length > 0) upload(files)
  }

  async function handleClear() {
    await clearHistory()
    onHistoryCleared()
  }

  return (
    <aside className="w-64 bg-gray-50 border-r border-gray-200 p-4 flex flex-col gap-4">
      <h1 className="text-xl font-bold">🍽️ PDF Eater</h1>

      <div>
        <button
          className="w-full bg-blue-600 text-white rounded px-3 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? '处理中…' : '上传 PDF'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
        {error && <p className="mt-2 text-red-600 text-xs">{error}</p>}
      </div>

      {loadedFiles.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-1">已加载</p>
          <ul className="text-sm text-gray-700 space-y-1">
            {loadedFiles.map((f) => (
              <li key={f} className="truncate">📄 {f}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="mt-auto text-sm text-gray-500 hover:text-gray-800 underline text-left"
        onClick={handleClear}
      >
        清除对话历史
      </button>
    </aside>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useUpload.js frontend/src/components/Sidebar.jsx
git commit -m "feat: Sidebar component with PDF upload and useUpload hook"
```

---

## Task 9: useChat hook + 聊天组件

**Files:**
- Create: `frontend/src/hooks/useChat.js`
- Create: `frontend/src/components/SourcesPanel.jsx`
- Create: `frontend/src/components/MessageBubble.jsx`
- Create: `frontend/src/components/ChatPane.jsx`

- [ ] **Step 1: 创建 `frontend/src/hooks/useChat.js`**

```javascript
import { useState, useCallback } from 'react'
import { streamChat } from '../api.js'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (question) => {
    setIsLoading(true)

    const userMsg = { role: 'user', content: question, sources: [] }
    const assistantMsg = { role: 'assistant', content: '', sources: [], isError: false }

    setMessages((prev) => [...prev, userMsg, assistantMsg])

    try {
      for await (const event of streamChat(question)) {
        if (event.type === 'token') {
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: updated[updated.length - 1].content + event.content,
            }
            return updated
          })
        } else if (event.type === 'sources') {
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              sources: event.content,
            }
            return updated
          })
        } else if (event.type === 'error') {
          setMessages((prev) => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: event.content,
              isError: true,
            }
            return updated
          })
        }
      }
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev]
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: e.message,
          isError: true,
        }
        return updated
      })
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearMessages = useCallback(() => setMessages([]), [])

  return { messages, isLoading, sendMessage, clearMessages }
}
```

- [ ] **Step 2: 创建 `frontend/src/components/SourcesPanel.jsx`**

```jsx
import { useState } from 'react'

export default function SourcesPanel({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-2">
      <button
        className="text-xs text-blue-600 hover:underline"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? '▲ 隐藏来源' : `▼ 查看来源（${sources.length}）`}
      </button>
      {open && (
        <ul className="mt-1 space-y-2">
          {sources.map((s, i) => (
            <li key={i} className="text-xs bg-gray-100 rounded p-2">
              <span className="font-semibold">第 {s.page} 页</span>
              <p className="text-gray-600 mt-1">{s.text}…</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

- [ ] **Step 3: 创建 `frontend/src/components/MessageBubble.jsx`**

```jsx
import SourcesPanel from './SourcesPanel.jsx'

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 text-sm ${
          isUser
            ? 'bg-blue-600 text-white'
            : message.isError
            ? 'bg-red-50 text-red-700 border border-red-200'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content || '▌'}</p>
        {!isUser && <SourcesPanel sources={message.sources} />}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 创建 `frontend/src/components/ChatPane.jsx`**

```jsx
import { useRef, useEffect, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'

export default function ChatPane({ messages, isLoading, onSend, hasDocuments }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSubmit(e) {
    e.preventDefault()
    const q = input.trim()
    if (!q || isLoading) return
    setInput('')
    onSend(q)
  }

  return (
    <div className="flex flex-col flex-1 h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-400 mt-16 text-sm">
            {hasDocuments ? '请输入问题开始对话' : '请先在左侧上传 PDF 文件'}
          </p>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-gray-200 p-4 flex gap-2">
        <input
          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          placeholder={hasDocuments ? '问关于 PDF 的问题…' : '请先上传 PDF'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading || !hasDocuments}
        />
        <button
          type="submit"
          className="bg-blue-600 text-white rounded px-4 py-2 text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          disabled={isLoading || !hasDocuments}
        >
          发送
        </button>
      </form>
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/useChat.js frontend/src/components/
git commit -m "feat: useChat hook and chat components (ChatPane, MessageBubble, SourcesPanel)"
```

---

## Task 10: App.jsx 组装 + 集成冒烟测试

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: 完善 `frontend/src/App.jsx`**

```jsx
import { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatPane from './components/ChatPane.jsx'
import { useChat } from './hooks/useChat.js'
import { getStatus } from './api.js'

export default function App() {
  const [loadedFiles, setLoadedFiles] = useState([])
  const { messages, isLoading, sendMessage, clearMessages } = useChat()

  useEffect(() => {
    getStatus()
      .then((s) => { if (s.loaded) setLoadedFiles(s.files) })
      .catch(() => {})
  }, [])

  function handleFilesLoaded(files) {
    setLoadedFiles(files)
    clearMessages()
  }

  function handleHistoryCleared() {
    clearMessages()
  }

  return (
    <div className="flex h-screen bg-white">
      <Sidebar
        loadedFiles={loadedFiles}
        onFilesLoaded={handleFilesLoaded}
        onHistoryCleared={handleHistoryCleared}
      />
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatPane
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
          hasDocuments={loadedFiles.length > 0}
        />
      </main>
    </div>
  )
}
```

- [ ] **Step 2: 同时启动后端和前端**

终端 1：
```bash
cd backend
uvicorn main:app --reload --port 8000
```

终端 2：
```bash
cd frontend
npm run dev
```

- [ ] **Step 3: 冒烟测试（手动）**

打开 `http://localhost:5173`，按顺序验证：

1. 页面显示 "PDF Eater"，右侧提示 "请先在左侧上传 PDF 文件"
2. 点击 "上传 PDF"，选择一个真实的可读 PDF 文件（任意有文字的 PDF）
3. Sidebar 出现文件名，处理完成后提示消失
4. 在输入框输入问题，点击发送
5. 右侧 AI 气泡出现并逐字打出答案（流式效果）
6. 答案下方出现 "查看来源" 链接，点击展开显示页码和摘录
7. 刷新页面 → 文件名消失但后端仍有 vectorstore（`GET /api/status` 返回 `loaded: true`）→ 输入问题仍可正常回答
8. 点击 "清除对话历史"，消息列表清空

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire App.jsx - full frontend integration complete"
```

---

## Task 11: 更新 .gitignore

**Files:**
- Modify: `.gitignore`（根目录）

- [ ] **Step 1: 确认 `data/` 和前端 `node_modules` 被忽略**

在根目录 `.gitignore` 中添加（如果不存在）：

```
# backend runtime data
backend/data/

# backend venv
backend/.venv/

# frontend
frontend/node_modules/
frontend/dist/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: update .gitignore for backend data and frontend node_modules"
```

---

## 自检记录

- [x] **Spec coverage：** 所有端点（upload、status、chat/stream、history）有对应 Task；FAISS 持久化在 Task 2+3；SSE 流式在 Task 5+9；Vite proxy 在 Task 6；错误处理在各 Task 中内联。
- [x] **Placeholder 扫描：** 无 TBD/TODO。
- [x] **类型一致性：** `app_state.chat_history` 在所有地方都是 `list[tuple[str, str]]`；`streamChat` generator 在 `api.js` 和 `useChat.js` 中使用的 event shape（`type`、`content`）一致；SSE 格式（`§3.3`）与 `chat.py` 中的 `yield` 语句一致。
