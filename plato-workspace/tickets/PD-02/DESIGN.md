# DESIGN.md

## Requirement

**原始需求**：项目目前后端用 Python、前端用 Streamlit，要改成前后端分离：后端用 FastAPI 暴露接口，前端用 React 做界面。本 ticket 只做后端部分——把后端服务封装成 FastAPI 接口。此改动是侵入性的，可以直接断开和 Streamlit 的连接。

**细化后的需求点**：

1. 所有前端需要的服务都通过 FastAPI 暴露成接口，包括：
   - 上传 PDF：校验可读性 → 加载切分 → 建向量库 → 建问答链
   - 问答：基于已加载文档、携带聊天历史进行提问
   - 聊天历史：查询与清空
   - 加载状态：当前是否已加载文档、已加载的文件列表（已有 `/api/status`）
   - 调试信息：最近一次检索的 query 与来源片段
2. 目前 `backend/` 下已有 FastAPI 应用骨架和一两个接口（`/api/status`），本次在其基础上补齐其余接口。
3. 直接删掉 Streamlit 入口，彻底断开与 Streamlit 的连接。

**是否需要 PM 确认**：不需要。

## External Dependencies

无外部依赖，无需任何人确认。

## Design

1. 梳理现有 Streamlit UI（`app.py`、`ui/sidebar.py`、`ui/chat.py`）中前端调用到的全部后端能力，作为接口清单。
2. 在现有 `backend/` FastAPI 应用上，按接口清单补齐 API：文件上传与处理、问答、历史管理、状态查询、调试信息。
3. 会话状态（问答链、已加载文件、历史、调试信息）由后端统一管理，前端只通过 API 交互。
4. 删除 Streamlit 入口（`app.py`）及 Streamlit UI 层（`ui/`），移除 Streamlit 相关依赖，完成与 Streamlit 的断开。
