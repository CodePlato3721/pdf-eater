## 编码规范

- **禁止 magic number / magic string**：数字或字符串字面量有语义时，必须提取为具名常量（`const` 对象 + `as const` 或普通 `const`）。仅在以下情况可直接使用字面量：值是辨别联合类型的 discriminant（如 `event.type === 'token'`），且只在一处出现、含义完全自明。
- **前端 TSX 保持轻量**：组件只负责渲染，状态、副作用、事件处理必须提取到 custom hook（`use*`）中。hook 放在与组件同目录或 `hooks/` 目录下，测试文件与 hook 同目录（`useXxx.test.ts`）。
- **前端单元测试采用 Chicago 派风格**：mock 只用于让被测代码能运行（隔离外部依赖、控制返回值），不断言 mock 被调用了多少次或以什么参数调用。只断言可观察的状态结果。
