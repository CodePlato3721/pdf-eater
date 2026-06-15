# Architecture

## 概述

PDF Eater 是一个 Streamlit 单体应用，允许用户上传 PDF 文件并通过对话方式提问。当前是单进程、无持久化状态的架构。

## 目录结构

```
pdf-eater/
├── app.py              # 入口：Streamlit 页面组装
├── config.py           # 全局常量（chunk size、model、top-k）
├── requirements.txt    # 依赖（当前为空，依赖通过 .venv 管理）
├── core/               # 业务逻辑层，不依赖 Streamlit
│   ├── loader.py       # PDF 读取、切分、可读性校验
│   ├── embeddings.py   # 向量化 & 向量库构建
│   └── chain.py        # LangChain 对话检索链
└── ui/                 # Streamlit UI 层
    ├── sidebar.py      # 文件上传、处理触发、历史清除、调试面板
    └── chat.py         # 会话状态初始化、对话渲染、问答调用
```

## 数据流

```
用户上传 PDF
    └─► ui/sidebar.py
            ├─► core/loader.py::is_readable()     # 可读性校验（pdfminer）
            ├─► core/loader.py::load_and_split()  # PDF → Documents → chunks
            ├─► core/embeddings.py::create_vectorstore()  # chunks → DocArrayInMemorySearch
            └─► core/chain.py::create_chain()     # vectorstore → ConversationalRetrievalChain
                    └─► 存入 st.session_state.qa

用户提问
    └─► ui/chat.py::render_chat()
            └─► st.session_state.qa.invoke({ question, chat_history })
                    ├─► ChatOpenAI (gpt-3.5-turbo) 生成答案
                    └─► 返回 answer + source_documents
```

## 关键技术

| 层级 | 技术 | 说明 |
|---|---|---|
| UI 框架 | Streamlit 1.56 | 页面渲染、session_state 管理 |
| PDF 解析 | pdfminer.six 20260107 | 文字提取，通过 PDFMinerLoader 加载 |
| 文本切分 | RecursiveCharacterTextSplitter | chunk_size=1000, overlap=150 |
| Embeddings | OpenAI Embeddings | text-embedding-ada-002（默认） |
| 向量库 | DocArrayInMemorySearch | 纯内存，进程退出即消失 |
| 检索链 | ConversationalRetrievalChain | langchain-classic，保留多轮对话历史 |
| LLM | ChatOpenAI gpt-3.5-turbo | temperature=0，top_k=4 |

## 状态管理

所有运行时状态存储在 `st.session_state`，无磁盘持久化：

| Key | 类型 | 说明 |
|---|---|---|
| `qa` | Chain \| None | 当前会话的检索链 |
| `chat_history` | list[tuple[str, str]] | (问题, 回答) 列表 |
| `loaded_files` | list[str] | 已加载的文件名列表 |
| `last_query` | str | 上一次 LLM 实际使用的问题（调试用） |
| `last_sources` | list[Document] | 上一次检索的来源文档 |

## 当前限制

- **无持久化**：刷新页面或重启服务后，向量库和对话历史全部丢失
- **内存向量库**：DocArrayInMemorySearch 不支持磁盘保存，文件量大时内存压力高
- **单用户**：session_state 是单进程级别，多用户会共享状态（Streamlit 多线程场景下有问题）
- **无流式输出**：LLM 回答是同步 invoke，等待期间无 token streaming
- **紧耦合**：`core/loader.py` 的接口接收 Streamlit `UploadFile` 对象，不便于测试和复用
