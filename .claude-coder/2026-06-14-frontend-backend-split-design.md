# PDF Eater — 前后端分离设计文档

**日期：** 2026-06-14  
**范围：** 将现有 Streamlit 单体应用拆分为 React 前端 + FastAPI 后端  
**用户场景：** 单用户，个人本地部署

---

## 1. 背景

现有应用是 Streamlit 单体，所有状态（vectorstore、chat_history、QA chain）存在 `st.session_state`。目标是将 UI 层替换为 React，业务逻辑暴露为 FastAPI REST/SSE 接口，同时支持 vectorstore 和对话历史持久化。

---

## 2. 整体架构

```
┌─────────────────────────────┐      ┌──────────────────────────────────┐
│       React Frontend         │      │        FastAPI Backend            │
│    localhost:5173            │      │       localhost:8000              │
│                              │      │                                  │
│  ┌──────────┐ ┌──────────┐  │      │  POST /api/upload                │
│  │ Sidebar  │ │ ChatPane │  │─────▶│  GET  /api/status                │
│  │(上传PDF) │ │(对话)    │  │      │  POST /api/chat/stream (SSE)     │
│  └──────────┘ └──────────┘  │◀─────│  DELETE /api/history             │
└─────────────────────────────┘      │                                  │
                                     │  ┌──────────┐  ┌─────────────┐  │
                                     │  │  core/   │  │  data/      │  │
                                     │  │  loader  │  │  faiss_idx/ │  │
                                     │  │  embeddi │  │  history.   │  │
                                     │  │  chain   │  │  json       │  │
                                     │  └──────────┘  └─────────────┘  │
                                     └──────────────────────────────────┘
```

**职责划分：**
- `core/` 目录（`loader.py`、`embeddings.py`、`chain.py`）保持不变，原封不动迁移至后端
- FastAPI 层只做 HTTP 适配，不含业务逻辑
- React 只做 UI 渲染和请求发送
- 持久化：vectorstore 存 `data/faiss_index/`，对话历史存 `data/history.json`

---

## 3. 后端设计（FastAPI）

### 3.1 目录结构

```
backend/
├── main.py              # FastAPI app，挂载路由，配置 CORS
├── config.py            # 常量（从现有 config.py 迁移）
├── routers/
│   ├── upload.py        # POST /api/upload
│   └── chat.py          # POST /api/chat/stream, DELETE /api/history
├── core/                # 直接迁移现有 core/
│   ├── chain.py
│   ├── embeddings.py
│   └── loader.py
├── state.py             # 全局单例：vectorstore + chain + chat_history
└── data/                # 运行时生成，gitignore
    ├── faiss_index/
    └── history.json
```

### 3.2 API 端点

| 方法 | 路径 | 作用 | 返回 |
|------|------|------|------|
| `POST` | `/api/upload` | 接收 PDF（multipart），处理、嵌入、保存 FAISS index | `{ "status": "ok", "files": ["a.pdf"] }` |
| `GET` | `/api/status` | 返回当前是否有已加载的 PDF | `{ "loaded": true, "files": ["a.pdf"] }` |
| `POST` | `/api/chat/stream` | 接收 `{ "question": "..." }`，SSE 流式返回 | SSE 流（见下） |
| `DELETE` | `/api/history` | 清空对话历史（内存 + history.json） | `{ "status": "ok" }` |

### 3.3 SSE 流格式（`/api/chat/stream`）

```
data: {"type": "token", "content": "根"}
data: {"type": "token", "content": "据文档"}
data: {"type": "sources", "content": [{"page": 3, "text": "..."}]}
data: {"type": "done"}
data: {"type": "error", "content": "OpenAI API 调用失败"}
```

### 3.4 全局状态（`state.py`）

全局单例持有三个对象：
- `chain`：LangChain ConversationalRetrievalChain 实例
- `chat_history`：`list[tuple[str, str]]`，与现有格式一致
- `loaded_files`：`list[str]`，已加载文件名

启动时检查 `data/faiss_index/` 是否存在，若存在则自动加载 vectorstore 并重建 chain；同时从 `data/history.json` 恢复对话历史。

### 3.5 vectorstore 变更

将 `DocArrayInMemorySearch` 替换为 `FAISS`：
- 保存：`vectorstore.save_local("data/faiss_index")`
- 加载：`FAISS.load_local("data/faiss_index", embeddings)`

`core/embeddings.py` 相应更新，其余 `core/` 文件不变。

---

## 4. 前端设计（React）

### 4.1 技术选型

- **Vite + React** — 脚手架
- **Tailwind CSS** — 样式
- **原生 `fetch` + `ReadableStream`** — 无第三方 HTTP/SSE 库（注：因聊天需要 POST 携带请求体，不使用仅支持 GET 的原生 `EventSource`）

### 4.2 目录结构

```
frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx              # 顶层布局（sidebar + chat）
│   ├── components/
│   │   ├── Sidebar.jsx      # PDF 上传、状态显示
│   │   ├── ChatPane.jsx     # 消息列表 + 输入框
│   │   ├── MessageBubble.jsx# 单条消息（含来源折叠展示）
│   │   └── SourcesPanel.jsx # 来源列表（可折叠）
│   ├── hooks/
│   │   ├── useUpload.js     # 封装 POST /api/upload 逻辑
│   │   └── useChat.js       # 封装 SSE 流式聊天逻辑
│   └── api.js               # 所有 fetch 调用的统一出口
├── index.html
└── vite.config.js           # proxy /api → localhost:8000
```

### 4.3 核心交互流程

1. 用户选择 PDF → `useUpload` 发 `POST /api/upload` → 成功后 Sidebar 显示文件名
2. 用户发问 → `useChat` 用 `fetch` POST `/api/chat/stream`，通过 `response.body.getReader()` 读取流
3. 收到 `token` → 追加到当前 assistant 气泡末尾（打字效果）
4. 收到 `sources` → 渲染来源折叠面板
5. 收到 `done` → reader 关闭，解锁输入框
6. 收到 `error` → 显示错误气泡，解锁输入框

### 4.4 状态管理

使用 React `useState`，无需 Redux/Zustand：
- `messages: Array<{role, content, sources}>` — 对话消息列表
- `isLoading: boolean` — 控制输入框禁用
- `loadedFiles: string[]` — 已上传文件名

### 4.5 Vite Proxy

`vite.config.js` 配置 `/api` → `http://localhost:8000`，前端代码直接调 `/api/...`，开发时规避 CORS，无需硬编码后端地址。

---

## 5. 错误处理

### 后端

| 场景 | 处理方式 |
|------|------|
| 上传的 PDF 无可读文字（扫描件） | 返回 `400` + `{ "detail": "文件不含可读文字" }` |
| 提问时未上传 PDF | 返回 `400` + `{ "detail": "未加载任何文档" }` |
| OpenAI API 调用失败 | SSE 推送 `{ "type": "error", "content": "..." }` |
| FAISS 文件损坏 | 启动时捕获异常，以空状态启动，记录日志 |
| 上传非 PDF 文件 | 校验 MIME type，返回 `400` |

### 前端

| 场景 | 处理方式 |
|------|------|
| 上传失败 | Sidebar 显示行内错误提示 |
| SSE `error` 事件 | 当前 assistant 气泡显示红色错误文字，输入框解锁 |
| 网络断开 | `EventSource.onerror` → 提示"连接中断，请重试" |
| 上传非 PDF | `<input accept=".pdf">` 前端过滤 |

**不在本次范围内（YAGNI）：**
- 上传进度条
- SSE 自动重连
- 离线缓存
- 多用户 / 身份认证

---

## 6. 迁移策略

现有 Streamlit 代码不删除，新建 `backend/` 和 `frontend/` 目录并行开发。`core/` 目录复制到 `backend/core/`。待前后端联调通过后，可删除 Streamlit 相关文件（`app.py`、`ui/`）。

---

## 7. 运行方式（开发）

```bash
# 后端
cd backend
uvicorn main:app --reload --port 8000

# 前端（另一个终端）
cd frontend
npm run dev          # 默认 localhost:5173
```
