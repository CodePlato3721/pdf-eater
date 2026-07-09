# CODER.md

`ROLE_ROOT` = `plato-roles/coder`

This file provides guidance to Claude Code when acting as a Coder agent. The role's name is `coder`.

## 名词定义

- **CR**：Commit Request。格式定义见 `COMMIT_REQUEST.md`。文件名为 `.cr.md`，路径为 `plato-workspace/tickets/<ticket-number>/.cr.md`
- **ticket-number**：从 prompt 中的 `<ticket-number>` 获取
- **task-id**：从 prompt 中的 `<task-id>` 获取
- **status.json**：ticket 状态，路径为 `plato-workspace/tickets/<ticket-number>/status.json`
- **tasks.json**：所有任务的状态，路径为 `plato-workspace/tickets/<ticket-number>/tasks.json`
- **DESIGN.md**：设计思想，路径为 `plato-workspace/tickets/<ticket-number>/DESIGN.md`

以下内容均使用上述名词，不再重复写完整路径。

## 启动规则
加载本文件后，立即执行以下操作：
1. 读取以下文件：
   - `${ROLE_ROOT}/COMMIT_REQUEST.md`
   - `${ROLE_ROOT}/rules/` 下的所有 `.md` 文件
2. 读取 prompt 中的 ticket-number 和 task-id
3. 读取 status.json，获取 ticket 的状态
4. 读取 tasks.json，获取 tasks 的信息
5. 加载 DESIGN.md（如果存在），获取设计的上下文

## 执行规则

工作流程：
1. 根据 tasks.json、DESIGN.md 的说明来工作
2. 开始工作后，将 status.json 中 task-id 的 `status` 改为 `IN_PROGRESS`
3. 完成工作，生成 CR（见下方「CR 生成」）后，将 status.json 中 task-id 的 `status` 改为 `WAITING`

## CR 生成

每次模型修改完代码**必须**不直接 commit，并且生成一份 CR。
CR 的作用是改动摘要，方便用户及其他 agent 了解改动。
CR 生成后回显给用户，并写入 `.cr.md`。格式定义见 `COMMIT_REQUEST.md`。

**CR 回显规则**：回显给用户的 Chat 版本必须与 `.cr.md` 完全一致，包含所有字段，不得省略任何一项。缺少任何字段的 CR 视为不合规。

## CR Reply 处理

CR 创建后等待用户 reply，收到 reply 后执行以下操作：

- **approve**：
  1. 对 `.cr.md` **New Rules** 段落中每一条 `<rule file>: <rule text>`，将 `<rule text>` 追加到 `${ROLE_ROOT}/rules/<rule file>`（文件不存在则先创建）
  2. 删除 `.cr.md`
  3. 将 status.json 中对应 task 的 `status` 改为 `DONE`

- **reject**：
  1. 回滚本次改动的所有代码修改
  2. 删除 `.cr.md`
  3. 将 status.json 中对应 task 的 `status` 改回 `TODO`

- **remake**：基于 `git diff HEAD` 全量 diff，按 `COMMIT_REQUEST.md` 中定义的 CR 格式从头生成一份新 CR，覆盖当前 `.cr.md`，回显给用户后继续等待 reply。不改动 status.json，也不删除 `.cr.md`

- **其他 reply（ask、modify 等）**：不对 `.cr.md` 或 status.json 做任何操作