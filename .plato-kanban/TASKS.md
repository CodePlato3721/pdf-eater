# PDF Eater — 任务清单

> 基于 [PLAN.md](PLAN.md) 拆分。每个 TASK 对应一个 CR，一句话可概括，改动可验证。

状态：`[ ]` 待做 · `[-]` 进行中 · `[x]` 完成

---

## [x] TASK-01 · 后端 core/ 层迁移

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

## [x] TASK-02 · FastAPI 骨架 + 状态层

**一句话**：首次引入 FastAPI，实现全局状态单例（含启动恢复逻辑）和状态查询端点。

**切分依据**：水平切分 — 首次引入 FastAPI 和全局状态模式，后续 TASK 在此基础上叠加功能。

**范围**
- `backend/main.py`：FastAPI app，配置 CORS，注册 lifespan startup hook
- `backend/state.py`：全局单例，持有 `chain`、`chat_history`、`loaded_files`；启动时若 `faiss_index/` 存在则调用 `load_vectorstore()` + `create_chain()` 恢复，FAISS 文件损坏时以空状态启动并记录日志；同时从 `history.json` 恢复 `chat_history`
- `GET /api/status`：返回 `{ loaded, files }`，作为状态层的脚手架出口

**验证**
- 单元测试 `tests/unit/test_state.py`：mock `load_vectorstore` + `create_chain`，验证 `restore()` 在 faiss_index 存在时调用了两者且 `state.chain` 被正确赋值；验证 faiss_index 不存在时 `state.chain` 为 None
- 人工：`uvicorn main:app` 启动无报错；`curl GET /api/status` 返回 `{"loaded": false, "files": []}`

session-id: 550e8400-e29b-41d4-a716-446655440002

---

## [ ] TASK-03 · 上传功能（后端）

**一句话**：实现 PDF 上传端点，打通从文件接收到 chain 就绪的完整链路。

**切分依据**：垂直切分 — 上传是第一个完整业务功能，复用 TASK-01 的 core 层和 TASK-02 的状态层。

**范围**
- `backend/routers/upload.py`
  - `POST /api/upload`：校验 MIME → `is_readable()` → `load_and_split()` → `create_vectorstore()` → `save_vectorstore()` → `create_chain()` → 更新 `state.chain` / `state.loaded_files`
  - 错误处理：非 PDF → 400；无可读文字 → 400

**验证**
- `curl` 上传合法 PDF → `data/faiss_index/` 目录生成 + `GET /api/status` 返回 `{"loaded": true, "files": ["xxx.pdf"]}`
- `curl` 上传非 PDF → 400；上传扫描件 → 400

session-id: 550e8400-e29b-41d4-a716-446655440003

---

## [ ] TASK-04 · 聊天功能（后端）

**一句话**：实现 SSE 流式聊天端点和清除历史端点。

**切分依据**：垂直切分 — 聊天是第二个完整业务功能，复用已有状态层和 chain。

**范围**
- `backend/routers/chat.py`
  - `POST /api/chat/stream`：SSE 流式推送 token / sources / done / error；每次回答后写入 `history.json`
  - `DELETE /api/history`：清空 `state.chat_history` + `history.json`
  - 未加载 PDF 时提问 → 400

**验证**
- `curl -N -X POST /api/chat/stream -d '{"question":"..."}' -H 'Content-Type: application/json'` 收到逐 token SSE 输出
- `DELETE /api/history` 后 `history.json` 清空或不存在

session-id: 550e8400-e29b-41d4-a716-446655440004

---

## [ ] TASK-05 · 前端基础层

**一句话**：首次引入 React，搭建前端脚手架和统一 API 调用层，用临时 DevPage 验证全链路连通。

**切分依据**：水平切分 — 首次引入 React + api.js 模式，后续 TASK 在此基础上叠加 UI 功能。

**范围**
- Vite + React + Tailwind CSS 初始化，清理脚手架默认内容
- `frontend/vite.config.js`：`/api` → `http://localhost:8000` proxy
- `frontend/src/api.js`：`getStatus`、`uploadPDF`、`clearHistory`、`streamChat`（ReadableStream SSE 解析）
- **临时脚手架** `frontend/src/DevPage.jsx`：调用 `api.getStatus()` 并将返回 JSON 渲染到页面，挂载到 `App.jsx`

**验证**
- `npm run dev` 启动无报错
- 浏览器打开 `localhost:5173`，页面显示 `{"loaded": false, "files": []}` — 证明 proxy + api.js 全链路通
- 验证后删除 `DevPage.jsx`，`App.jsx` 还原为空占位

session-id: 550e8400-e29b-41d4-a716-446655440005

---

## [ ] TASK-06 · 上传功能 UI

**一句话**：实现上传 hook 和 Sidebar 组件。

**切分依据**：垂直切分 — 上传 UI 是第一个前端业务功能，复用 TASK-05 的 api.js。

**范围**
- `frontend/src/hooks/useUpload.js`：`upload(file)`、`loadedFiles`、`isUploading`、`error`；挂载时调用 `getStatus()` 初始化
- `frontend/src/components/Sidebar.jsx`：文件选择（`accept=".pdf"`）、上传 loading、已加载文件列表、行内错误提示、清除历史按钮

**验证**（人工，前后端均启动）
- 上传 PDF → Sidebar 显示文件名
- 上传非 PDF → 行内错误提示
- 点击清除历史 → 文件名消失

session-id: 550e8400-e29b-41d4-a716-446655440006

---

## [ ] TASK-07 · 聊天功能 UI

**一句话**：实现流式聊天 hook 和聊天区全部组件，完成顶层布局整合。

**切分依据**：垂直切分 — 聊天 UI 是第二个前端业务功能，复用 TASK-05 的 api.js 和 TASK-06 的 Sidebar。

**范围**
- `frontend/src/hooks/useChat.js`：`sendMessage`、`clearHistory`、`messages`、`isLoading`；处理 token / sources / done / error 四种 SSE 事件
- `frontend/src/components/MessageBubble.jsx`：user / assistant 气泡样式，错误状态红色显示
- `frontend/src/components/SourcesPanel.jsx`：来源列表折叠展示
- `frontend/src/components/ChatPane.jsx`：消息列表、自动滚底、输入框、发送按钮（loading 时禁用）
- `frontend/src/App.jsx`：Sidebar + ChatPane 顶层布局

**验证**（人工，前后端均启动）
- 上传 PDF 后发问，token 逐字追加（打字效果）
- sources 折叠面板正常展开/收起
- 回答完成前输入框禁用

session-id: 550e8400-e29b-41d4-a716-446655440007

---

## [ ] TASK-08 · 清理 Streamlit 代码

**一句话**：联调通过后删除 Streamlit 相关文件并更新架构文档。

**范围**
- 删除 `app.py`、`ui/` 目录
- 从根 `pyproject.toml` 移除 `streamlit` 依赖，`uv sync`
- 更新 `CLAUDE.md`、`doc/ARCHITECTURE.md` 反映新架构

**验证**：`uv sync` 输出不含 streamlit；`uvicorn main:app` + `npm run dev` 正常启动；项目根无 `app.py`

session-id: 550e8400-e29b-41d4-a716-446655440008

---

> **执行顺序**
> ```
> TASK-01 → TASK-02 → TASK-03 → TASK-04   （后端，顺序执行）
>                   ↓
>              TASK-05 → TASK-06 → TASK-07  （前端，TASK-02 完成后可并行开始）
>                                    ↓
>                               TASK-08     （联调通过后）
> ```
