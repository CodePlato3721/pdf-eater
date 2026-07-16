---
name: plato
description: Entry point for the Plato ticket workflow (designer/planner/coder role pipeline under plato-workspace/tickets). Creates a new ticket workspace or reports the current state of an existing one and produces the exact `claude -p` / `claude --resume` command to run next.
disable-model-invocation: true
---

# Plato

Plato is this repo's ticket-driven development framework. Work on a Jira-style
ticket is organized under `plato-workspace/tickets/<ticket-number>/` and moves
through three roles, in order: **designer → planner → coder**. Each role is
run as a separate `claude` CLI invocation with its own session, described by
`.plato/<role>/<ROLE>.md`.

## Role status states

Each role (and each coder task) has a `status` field with one of four values:

| Status | Meaning |
|---|---|
| `TODO` | Not started yet. |
| `IN_PROGRESS` | Running right now in the background. |
| `WAITING` | Finished its current run and is waiting for the user to resume the session and interact. |
| `DONE` | Fully complete. |

## Role → file mapping

| role | append-system-prompt-file |
|---|---|
| `designer` | `.plato/designer/DESIGNER.md` |
| `planner` | `.plato/planner/PLANNER.md` |
| `coder` | `.plato/coder/CODER.md` |

---

## Entry point: `/plato <ticket-number>`

### Step 1 — Resolve the ticket number

If the skill was invoked with an argument, that's the ticket number. If not,
ask the user: "What is the ticket number?" and wait for the answer.

### Step 2 — New or existing?

If `plato-workspace/tickets/` doesn't exist yet (first-ever ticket in this
repo), create it before checking further.

Check whether `plato-workspace/tickets/<ticket-number>/status.json` exists.

- Does not exist → **Creation flow**
- Exists → **Continue flow**

---

## Creation flow

See `skills/plato/references/CREATION_FLOW.md`.

---

## Continue flow

See `skills/plato/references/CONTINUE_FLOW.md`.
