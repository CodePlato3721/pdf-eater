# Architecture

## 概述

PDF Eater 是一个 PDF 问答应用：**React 18 + Vite 前端** + **FastAPI 后端**，前后端通过 REST API 通信。后端用 LangChain + FAISS 做检索增强问答（RAG），状态是进程级单例、持久化到本地磁盘（FAISS 索引 + 聊天历史 JSON），非多用户隔离。

## 目录结构

```
pdf-eater/
├── backend/
│   ├── main.py              # 入口：FastAPI 路由 + 异常翻译
│   ├── config.py            # 全局常量（chunk size、model、top-k、相似度阈值）
│   ├── core/                # 领域能力层，无状态
│   │   ├── loader.py        # PDF 读取、按页加载、切分、可读性校验
│   │   ├── embeddings.py    # 向量化 & FAISS 索引构建/存取
│   │   ├── chain.py         # LangChain 对话检索链 + QA prompt
│   │   ├── citation.py      # 从检索结果中定位支持答案的原文片段
│   │   ├── similarity.py    # 词袋余弦相似度（citation 用）
│   │   └── http_logging.py  # LLM/embedding HTTP 请求日志
│   ├── services/            # 业务编排层
│   │   ├── ingestion.py     # 上传管道 + 启动时恢复
│   │   ├── qa.py            # 问答业务逻辑
│   │   └── state.py         # 进程级状态容器 + 自持久化
│   └── data/                 # 运行时持久化：faiss_index/、history.json
└── frontend/
    └── src/
        ├── api/              # fetch 封装（client.ts、chat.ts、documents.ts）
        ├── hooks/            # 状态 + 副作用（useChat、useDocuments、useQuestionForm...）
        ├── components/       # 纯渲染组件（Sidebar、ChatArea）
        └── App.tsx           # 组装 hooks 和组件
```

## 数据流

```
上传 PDF
    └─► POST /api/upload
            └─► services/ingestion.py::ingest()
                    ├─► core/loader.py::is_readable()      # 可读性校验（pdfminer）
                    ├─► core/loader.py::load_and_split()   # PDFMinerLoader(mode="page") → 按页 Document → chunks
                    ├─► core/embeddings.py                 # chunks → FAISS 索引，落盘到 data/faiss_index
                    └─► core/chain.py::create_chain()       # vectorstore → ConversationalRetrievalChain
                            └─► 存入 state.chain（services/state.py 单例）

提问
    └─► POST /api/ask
            └─► services/qa.py::ask()
                    ├─► state.chain.invoke({question, chat_history})
                    │       ├─► 浓缩问题+历史为独立检索问句
                    │       ├─► FAISS 相似度检索（k=4）
                    │       └─► ChatOpenAI(gpt-3.5-turbo) 依据检索到的 4 个 chunk 生成答案
                    ├─► core/citation.py::build_citation_block()  # 词袋余弦相似度在检索句子池中定位支持答案的原句，拼出「Source (page N): 引用」块
                    ├─► 追加 (question, answer+citation) 到 state.chat_history，持久化到 data/history.json
                    └─► 返回 answer 文本
```

前端侧：`useDocuments`/`useChat` 两个 hook 分别负责文档状态和对话状态，挂载时各自拉 `/api/status`、`/api/history` 回填；`ask()`/`uploadFiles()` 乐观更新本地状态后再等待后端响应；`App.tsx` 把状态和回调传给纯渲染组件 `Sidebar`/`ChatArea`。

## 关键技术

| 层级 | 技术 | 说明 |
|---|---|---|
| 前端框架 | React 18 + Vite | hooks 管理状态，组件只管渲染 |
| 后端框架 | FastAPI | 路由层只做 HTTP 映射和异常翻译 |
| PDF 解析 | pdfminer.six，通过 `PDFMinerLoader(mode="page")` | 按页加载，保留页码 metadata |
| 文本切分 | RecursiveCharacterTextSplitter | chunk_size=1000, overlap=150 |
| Embeddings | OpenAI Embeddings | 默认模型 |
| 向量库 | FAISS | 持久化到 `backend/data/faiss_index` |
| 检索链 | ConversationalRetrievalChain（langchain-classic） | 保留多轮对话历史，search_type="similarity", k=4 |
| LLM | ChatOpenAI gpt-3.5-turbo | temperature=0；自定义 prompt 禁止使用训练知识回答 |
| 引用定位 | 词袋余弦相似度（`core/similarity.py`） | 非语义 embedding，在检索到的句子池中找与答案最相似的句子作为引用来源 |

## 状态管理

所有运行时状态存储在后端 `services/state.py::AppState` 单例中，持久化到磁盘（非多用户隔离）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `chain` | Chain \| None | 当前检索链（上传文档后建立） |
| `chat_history` | list[tuple[str, str]] | (问题, 回答) 列表，持久化到 `data/history.json` |
| `loaded_files` | list[str] | 已加载的文件名列表 |
| `last_query` | str | 上一次 LLM 实际使用的检索问句（`/api/debug` 调试用） |
| `last_sources` | list[dict] | 上一次检索的来源片段（`/api/debug` 调试用） |

前端不保存独立状态副本——`useChat`/`useDocuments` 在挂载时从后端拉取当前状态。

## 当前限制

- **单进程、非多用户隔离**：`AppState` 是进程级单例，多用户会共享同一份文档和对话历史
- **引用定位是词袋相似度，非语义匹配**：对同义改写、别名（如 "Jo"/"Josephine"）的召回弱，已知会漏引用（见 `plato-workspace/backlogs/PD-09.md`）
- **无章节级引用**：只有页码，没有章节信息（见 `plato-workspace/backlogs/PD-04.md`）
- **无流式输出**：LLM 回答是同步 `invoke`，等待期间无 token streaming
- **检索召回上限受 k=4 限制**：纯向量相似度检索，对生僻字面量匹配效果差，PD-09 记录过混合检索（BM25+FAISS）的后续方案
