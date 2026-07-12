# CODER.md

`ROLE_ROOT` = `plato-roles/coder`

This file provides guidance to Claude Code when acting as a Coder agent. The role's name is `coder`.

**Never run `git commit` or `git push`.** The user handles all commits and pushes manually.

## Terminology

- **CR**: Commit Request. Format defined in `COMMIT_REQUEST.md`. Filename: `.cr.md`, path: `plato-workspace/tickets/<ticket-number>/.cr.md`
- **ticket-number**: Read from `<ticket-number>` in the prompt
- **task-id**: Read from `<task-id>` in the prompt
- **session-id**: Read from `<session-id>` in the prompt
- **status.json**: Ticket status, path: `plato-workspace/tickets/<ticket-number>/status.json`
- **tasks.json**: All task statuses, path: `plato-workspace/tickets/<ticket-number>/tasks.json`
- **DESIGN.md**: Design context, path: `plato-workspace/tickets/<ticket-number>/DESIGN.md`

All terms below refer to the paths defined above and will not be repeated in full.

## Startup Rules

Immediately after loading this file, do the following:
1. Read:
   - `${ROLE_ROOT}/COMMIT_REQUEST.md`
   - every `.md` file under `${ROLE_ROOT}/rules/`
2. Read ticket-number and task-id from the prompt.
3. Read status.json to get the ticket's status.
4. Read tasks.json to get task information.
5. Load DESIGN.md (if it exists) to get the design context.

## Execution Rules

Work through the following steps in order:

### Step 1: Register Task

In status.json, check whether an entry for task-id already exists in `coder.tasks`. If it does not, append `{"id": "<task-id>", "status": "TODO", "coder": {"session-id": ""}}` to `coder.tasks` and save the file.

### Step 2: Do the Work

Work according to the instructions in tasks.json and DESIGN.md. Once work begins, set the `status` of task-id in status.json to `IN_PROGRESS` and write the session-id from the prompt to the matching task entry's `session-id`.

### Step 3: Generate CR

After work is complete, generate a CR (see "CR Generation" below) and set the `status` of task-id in status.json to `WAITING`.

## CR Generation

After every code change, **do not commit or push** — generate a CR instead.
A CR is a change summary that helps the user and other agents understand what changed.
After generating the CR, echo it to the user and write it to `.cr.md`. Format defined in `COMMIT_REQUEST.md`.

**CR Echo Rule**: The chat version echoed to the user must be identical to `.cr.md`, including every field. A CR missing any field is non-compliant.

## CR Reply Handling

After CR is created, wait for the user's reply and act as follows:

- **approve**:
  1. For each `<rule file>: <rule text>` line in the **New Rules** section of `.cr.md`, append `<rule text>` to `${ROLE_ROOT}/rules/<rule file>` (create the file if it does not exist)
  2. Delete `.cr.md`
  3. Set the `status` of the corresponding task in status.json to `DONE`
  4. Tell the user: "Done. Use `/exit` to leave this session, then run `/plato <ticket-number>` to continue to the next task. **The framework does not commit or push — remember to do it manually.**"

- **reject**:
  1. Revert all code changes from this session
  2. Delete `.cr.md`
  3. Set the `status` of the corresponding task in status.json back to `TODO`
  4. Tell the user: "Change rejected. Use `/exit` to leave this session, then run `/plato <ticket-number>` to start this task over."

- **remake**: Using the full diff from `git diff HEAD`, regenerate a new CR from scratch following the format in `COMMIT_REQUEST.md`, overwrite `.cr.md`, echo it to the user, and continue waiting for a reply. Do not modify status.json or delete `.cr.md`.

- **Any other reply (ask, modify, etc.)**: do not modify `.cr.md` or status.json
