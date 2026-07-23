---
name: plato
description: Entry point for the Plato ticket workflow (designer/planner/coder role pipeline for features, fixer role pipeline for defects, under plato-workspace/tickets). Creates a new ticket workspace or reports the current state of an existing one and produces the exact `claude -p` / `claude --resume` command to run next.
disable-model-invocation: true
---

# Plato

Plato is this repo's ticket-driven development framework. Work on a Jira-style
ticket is organized under `plato-workspace/tickets/<ticket-number>/`.

## Entry point: `/plato <ticket-number>`

## Ticket Types

Every ticket has a `type` — `feature` or `defect` — and each type moves
through its own role pipeline. Each role is run as a separate `claude` CLI
invocation with its own session, described by `.plato/<role>/<ROLE>.md`.

### Feature

Feature tickets move through three roles, in order: **designer → planner → coder**.

#### Role → file mapping

| role | append-system-prompt-file |
|---|---|
| `designer` | `.plato/designer/DESIGNER.md` |
| `planner` | `.plato/planner/PLANNER.md` |
| `coder` | `.plato/coder/CODER.md` |

### Defect

Defect tickets move through a single role: **fixer** — diagnosis, fix, and
verification all happen in one session, with no separate design/planning phase.

#### Role → file mapping

| role | append-system-prompt-file |
|---|---|
| `fixer` | `.plato/fixer/FIXER.md` |

## Role status states

Each role (and each coder task) has a `status` field with one of four values:

| Status | Meaning |
|---|---|
| `TODO` | Not started yet. |
| `IN_PROGRESS` | Running right now in the background. |
| `WAITING` | Finished its current run and is waiting for the user to resume the session and interact. |
| `DONE` | Fully complete. |

## Execute Steps

### Step 1 — Resolve the ticket number

If the skill was invoked with an argument, that's the ticket number. If not,
ask the user: "What is the ticket number?" and wait for the answer.

### Step 2 — New or existing?

If `plato-workspace/tickets/` doesn't exist yet (first-ever ticket in this
repo), create it before checking further.

Check whether `plato-workspace/tickets/<ticket-number>/status.json` exists.

- Does not exist → go to Step 3a (new)
- Exists → go to Step 3b (existing)

### Step 3a — New: determine ticket type, then create

Ask the ticket type. Use `AskUserQuestion` with two options: `feature` and
`defect`. Then:

- `feature` → **Feature Creation Flow**
- `defect` → **Defect Creation Flow**

### Step 3b — Existing: read ticket type, then continue

Read the `type` field from `plato-workspace/tickets/<ticket-number>/status.json`. Then:

- `feature` → **Feature Continue Flow**
- `defect` → **Defect Continue Flow**

### Feature Creation Flow

See `skills/plato/references/FEATURE_CREATION_FLOW.md`.

### Defect Creation Flow

See `skills/plato/references/DEFECT_CREATION_FLOW.md`.

### Feature Continue Flow

See `skills/plato/references/FEATURE_CONTINUE_FLOW.md`.

### Defect Continue Flow

See `skills/plato/references/DEFECT_CONTINUE_FLOW.md`.
