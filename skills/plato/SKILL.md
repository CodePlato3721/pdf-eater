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
`plato-roles/<role>/<ROLE>.md`.

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
| `designer` | `plato-roles/designer/DESIGNER.md` |
| `planner` | `plato-roles/planner/PLANNER.md` |
| `coder` | `plato-roles/coder/CODER.md` |

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

1. Ask the ticket type. Use `AskUserQuestion` with two options: `feature` and
   `defect`.
2. Ask the ticket title (free text): "What is the title of this ticket?"
3. Create `plato-workspace/tickets/<ticket-number>/` if it doesn't exist, and
   copy `skills/plato/status.default.json` into it as `status.json`.
4. Edit the new `status.json`:
   - set `type` to the chosen type
   - set `title` to the given title
5. Generate a session id (a UUID) to use in the command below by running
   `python skills/plato/scripts/gen_session_id.py`.
   Do not write it into `status.json` — leave `designer.session-id` empty for
   now.
6. Tell the user the ticket workspace was created, and give them the command
   to kick off the designer role:

   ```
   claude -p --session-id "<session-id>" --append-system-prompt-file "plato-roles/designer/DESIGNER.md"
   ```

---

## Continue flow

### Step 1 — Report current status

Run `python skills/plato/scripts/status_report.py <ticket-number>` and show
its output to the user as-is. It reads
`plato-workspace/tickets/<ticket-number>/status.json` and formats it as:

```
ticket number: <ticket number>
title: <title>
designer: <role status>
planner: <role status>
coder: <role status>
tasks:
<task id1>: <role status>
<task id2>: <role status>
...
```

(`tasks` comes from `coder.tasks[]`; if the list is empty it prints
`tasks: (none yet)`.)

### Step 2 — Find the active step

Run `python skills/plato/scripts/find_active_step.py <ticket-number>`. It
walks the roles in order (designer → planner → coder), skipping any whose
status is `DONE`. For coder, `coder.tasks[]` in `status.json` is treated as
an append-only log rather than a one-time snapshot of `tasks.json` — since
`tasks.json` can keep changing while tasks are in flight, it's read
incrementally instead of bootstrapped all at once:

1. Look at the *last* entry in `coder.tasks[]` whose status isn't `DONE`. If
   found, that's the active task.
2. If every tracked entry is `DONE` (or none are tracked yet), find the
   first task in `plato-workspace/tickets/<ticket-number>/tasks.json` whose
   `id` isn't already in `coder.tasks[]`, append it as a new `TODO` entry,
   persist that back into `status.json`, and use it as the active task.

It prints four lines:

```
role: <designer|planner|coder|none>
task-id: <task id, only set when role is coder>
status: <TODO|IN_PROGRESS|WAITING|DONE>
session-id: <value, or empty>
```

If `role` is `none` (status will be `DONE`), the ticket is fully complete —
tell the user that and stop, no command to generate.

### Step 3 — Generate the command

Run `python skills/plato/scripts/generate_command.py <ticket-number> <role> <status> <session-id> [task-id]`
using the four values Step 2 reported (`task-id` only needed when `role` is
`coder`), and show its output to the user as-is.

If `status` is `TODO` and `session-id` was empty, the script generates a new
UUID itself, persists it into `status.json` at the correct path
(`designer.session-id`, `planner.session-id`, or, for a coder task, the
`coder.session-id` of the matching task), and uses it in the printed
command. Never generate or fabricate a `session-id` yourself — the script is
the only place that does that.
