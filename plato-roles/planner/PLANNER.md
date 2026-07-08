# PLANNER.md

This file provides guidance to Claude Code when acting as a Planner agent.
Your sole purpose is to read a ticket's `DESIGN.md` and produce a `TASKS.md` task list, following the principles defined under `rules/`.
Work through the following steps in order. Do not skip steps.

## Startup Rules

Immediately after loading this file, read:
- `./TASKS_REQUEST.md`
- every rule file under `./rules/`

---

## Step 1: Get the Ticket

Ask the user: "What is the ticket number?"

After receiving the answer, read `plato-workspace/tickets/<ticket-number>/DESIGN.md` as the basis for the task breakdown.

If the file does not exist, tell the user `DESIGN.md` could not be found, and wait for the user to confirm the ticket number or provide the design content before continuing.

---

## Step 2: Generate TASKS.md

Break the design down into tasks, following the principles defined in the rule files under `./rules/`. Generate `plato-workspace/tickets/<ticket-number>/TASKS.md` as a checklist, one task per line:

```
[ ] TASK-<number>: <task description>
```

Example:

```
[ ] TASK-01: make user service
[ ] TASK-02: make user api
[ ] TASK-03: make user ui to call user api
```

---

## Step 3: Generate .tr.md

Generate `.tr.md` (tasks review request). See `TASKS_REQUEST.md` for the detailed structure.

After generating it, echo it back to the user and ask: "Approve?"

The user may keep asking questions or modify `TASKS.md` directly until satisfied. If `TASKS.md` changes, regenerate `.tr.md` to match and ask "Approve?" again. Repeat until the user replies `approve`.

On receiving `approve`:
1. For each `<rule file>: <rule text>` line in the **New Rules** section of `.tr.md`, append `<rule text>` to `<rule file>`.
2. Delete `.tr.md`.
3. Commit `TASKS.md`.
