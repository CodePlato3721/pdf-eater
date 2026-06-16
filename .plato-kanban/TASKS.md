# PDF Eater — 任务清单

> 基于 [PLAN.md](PLAN.md) 拆分。每个 TASK 对应一个 CR，一句话可概括，改动可验证。

状态：`[ ]` 待做 · `[-]` 进行中 · `[x]` 完成

---

## [ ] TASK-01 · 后端 core/ 层迁移

**一句话**：将现有 `core/` 迁移至 `backend/core/`，并将向量库从 DocArrayInMemorySearch 替换为 FAISS。

**范围**（业务逻辑层）
- 创建 `backend/` 目录结构及 `pyproject.toml` 后端依赖
- `backend/core/loader.py`：接口由 Streamlit `UploadedFile` 改为 `bytes`
- `backend/core/embeddings.py`：替换为 FAISS，新增 `save_vectorstore` / `load_vectorstore`
- `backend/core/chain.py`：原样迁移
- `backend/config.py`：迁移常量，新增 `FAISS_INDEX_PATH`、`HISTORY_PATH`

**验证**：单元测试 `tests/unit/test_core.py`，覆盖 `load_and_split`、`create_vectorstore`、`save/load_vectorstore`

session-id: 550e8400-e29b-41d4-a716-446655440001

---

## [ ] TASK-02 · FastAPI 项目骨架 + 全局状态

**一句话**：初始化 FastAPI 项目骨架，实现启动时自动恢复 FAISS index 和对话历史的全局状态单例。

**范围**（应用初始化层）
- `backend/state.py`：全局单例，持有 `chain`、`chat_history`、`loaded_files`；启动时恢复 `faiss_index/` 和 `history.json`，FAISS 文件损坏时以空状态启动
- `backend/main.py`：FastAPI app，配置 CORS，触发 state 初始化

**验证**：`uvicorn main:app` 启动无报错；放置已有 faiss_index 后重启，确认 `state.loaded_files` 非空

---

## [ ] TASK-03 · 上传 & 状态 API

**一句话**：实现 PDF 上传端点和当前状态查询端点。

**范围**（HTTP API 层 — upload router）
- `backend/routers/upload.py`
  - `POST /api/upload`：校验 MIME、调用 core 解析嵌入、保存 FAISS、更新 state
  - `GET /api/status`：返回 `{ loaded, files }`
- 错误处理：非 PDF → 400；无可读文字 → 400

**验证**：`curl` 上传合法 PDF 确认 faiss_index 生成；上传非 PDF / 扫描件确认正确报错

---

## [ ] TASK-04 · 聊天 & 历史 API

**一句话**：实现 SSE 流式聊天端点和清除对话历史端点。

**范围**（HTTP API 层 — chat router）
- `backend/routers/chat.py`
  - `POST /api/chat/stream`：SSE 流式推送 token / sources / done / error；每次回答后写入 `history.json`
  - `DELETE /api/history`：清空内存 + `history.json`
- 未加载 PDF 时提问 → 400

**验证**：`curl -N POST /api/chat/stream` 收到逐 token SSE 输出；`DELETE /api/history` 后 `history.json` 清空

---

## [ ] TASK-05 · 前端项目初始化 + API 调用层

**一句话**：初始化 React 前端项目并实现统一的后端 API 调用层。

**范围**（前端基础设施层）
- Vite + React + Tailwind CSS 初始化，清理脚手架默认内容
- `vite.config.js`：`/api` → `http://localhost:8000` proxy
- `frontend/src/api.js`：`uploadPDF`、`getStatus`、`clearHistory`、`streamChat`（ReadableStream SSE 解析）

**验证**：`npm run dev` 启动无报错；在浏览器 DevTools 手动调用 `api.getStatus()` 确认 proxy 正确转发

---

## [ ] TASK-06 · 上传功能 UI（Sidebar）

**一句话**：实现 PDF 上传的 hook 和 Sidebar 组件。

**范围**（前端 — 上传功能）
- `frontend/src/hooks/useUpload.js`：`upload(file)`、`loadedFiles`、`isUploading`、`error`；挂载时调用 `getStatus()` 初始化
- `frontend/src/components/Sidebar.jsx`：文件选择（`accept=".pdf"`）、上传 loading、已加载文件列表、行内错误提示、清除历史按钮

**验证**：启动前后端，在 Sidebar 上传 PDF 确认文件名显示；上传非 PDF 确认错误提示；点击清除历史后文件名消失

---

## [ ] TASK-07 · 聊天功能 UI（ChatPane）

**一句话**：实现流式聊天的 hook 和聊天区全部组件，并在 App.jsx 完成顶层布局整合。

**范围**（前端 — 聊天功能）
- `frontend/src/hooks/useChat.js`：`sendMessage`、`clearHistory`、`messages`、`isLoading`；处理 token / sources / done / error 四种 SSE 事件
- `frontend/src/components/MessageBubble.jsx`：user / assistant 气泡样式，错误状态红色显示
- `frontend/src/components/SourcesPanel.jsx`：来源列表折叠展示
- `frontend/src/components/ChatPane.jsx`：消息列表、自动滚底、输入框、发送按钮（loading 时禁用）
- `frontend/src/App.jsx`：Sidebar + ChatPane 顶层布局

**验证**：上传 PDF 后发问，确认 token 逐字追加（打字效果）、sources 折叠面板正常、输入框在回答完成前禁用

---

## [ ] TASK-08 · 清理 Streamlit 代码

**一句话**：联调通过后删除 Streamlit 相关文件并更新架构文档。

**范围**（配置 + 文档层）
- 删除 `app.py`、`ui/` 目录
- 从 `pyproject.toml` 移除 `streamlit` 依赖，`uv sync`
- 更新 `CLAUDE.md`、`doc/ARCHITECTURE.md` 反映新架构

**验证**：`uv sync` 无 streamlit；`uvicorn` + `npm run dev` 正常启动，项目根不再有 `app.py`

---

> **执行顺序**
> ```
> TASK-01 → TASK-02 → TASK-03 → TASK-04   （后端，顺序执行）
>                   ↓
>              TASK-05 → TASK-06 → TASK-07  （前端，TASK-02 完成后可并行开始）
>                                    ↓
>                               TASK-08     （联调通过后）
> ```
