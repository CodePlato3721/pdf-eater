# CODER.md

`ROLE_ROOT` = `plato-roles/coder`

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 启动规则
加载本文件后，立即读取以下文件：
- `${ROLE_ROOT}/CR.md`
- `${ROLE_ROOT}/RULES.md`

## Workflow Rules

- **Never commit changes directly.** After making any code modifications, stop and wait for the user to review the diff before creating any git commit.

## 决策规则
遇到需要在多个方案之间选择时，不要反复尝试，立即停止并将问题写入 
.plato-kanban/BLOCKED.md，格式如下：

## BLOCKED
- Task: TASK-01
- 问题描述: xxx
- 方案A: xxx
- 方案B: xxx

写完后退出，等待人工决策。