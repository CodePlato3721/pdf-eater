## CR · TASK-02 · FastAPI 骨架 + 状态层

**Type**: feature

---

**Design**: 首次引入 FastAPI，实现全局状态单例（含启动恢复逻辑）和状态查询端点 `GET /api/status`。启动时若 `data/faiss_index/` 存在则自动恢复 chain；FAISS 损坏时以空状态启动并记录日志；同时从 `data/history.json` 恢复 `chat_history`。

**Source Details**:
```python
# state.py — restore() 核心逻辑
if os.path.isdir(FAISS_INDEX_PATH):
    vectorstore = load_vectorstore(FAISS_INDEX_PATH)
    self.chain = create_chain(vectorstore)
```

**Source Tree**:
```
backend/
├── main.py              ← new（FastAPI app，CORS，lifespan hook，GET /api/status）
├── state.py             ← new（AppState 单例，restore() 恢复逻辑）
└── core/
    └── chain.py         ← updated（create_chain 参数加 VectorStore 类型注解）
```

**Test Details**: 新增 `test_state.py`，通过 `patch.object` mock `load_vectorstore` 和 `create_chain`，覆盖 `AppState.restore()` 的 5 个场景：
1. faiss_index 存在 → 两者均被调用，`state.chain` 正确赋值
2. faiss_index 不存在 → 两者均未调用，`state.chain` 为 None
3. FAISS 损坏（load 抛异常）→ 不抛出，`state.chain` 为 None
4. history.json 存在 → `chat_history` 从文件恢复
5. history.json 不存在 → `chat_history` 为空列表

同步精简了 `conftest.py`，移除了针对已删除的根目录 `config.py` / `core/` 的 workaround。

**Test Tree**:
```
tests/
├── conftest.py          ← updated（精简，移除旧 workaround）
└── unit/
    └── test_state.py    ← new
```

**Test Result**: 16 passed, 0 failed
```
tests/unit/test_core.py   11 passed
tests/unit/test_state.py   5 passed
```

---

**Reply**: approve
