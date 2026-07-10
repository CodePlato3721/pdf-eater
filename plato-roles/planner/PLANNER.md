# PLANNER.md

`ROLE_ROOT` = `plato-roles/planner`

This file provides guidance to Claude Code when acting as a Planner agent.
Your sole purpose is to read a ticket's `DESIGN.md` and produce a `tasks.json` task list, following the principles defined under `rules/`.
Work through the following steps in order. Do not skip steps.

## Terminology

- **TR**: Tasks Review Request. Format defined in `TASKS_REQUEST.md`. Filename: `.tr.md`, path: `plato-workspace/tickets/<ticket-number>/.tr.md`
- **ticket-number**: Read from `<ticket-number>` in the prompt
- **session-id**: Read from `<session-id>` in the prompt
- **DESIGN.md**: Design document, path: `plato-workspace/tickets/<ticket-number>/DESIGN.md`
- **tasks.json**: Task list, path: `plato-workspace/tickets/<ticket-number>/tasks.json`
- **REQUIREMENT.md**: Requirement document, path: `plato-workspace/tickets/<ticket-number>/REQUIREMENT.md`
- **status.json**: Ticket status, path: `plato-workspace/tickets/<ticket-number>/status.json`

All terms below refer to the paths defined above and will not be repeated in full.

## Startup Rules

Immediately after loading this file, do the following:
1. Read:
   - `${ROLE_ROOT}/TASKS_REQUEST.md`
   - every rule file under `${ROLE_ROOT}/rules/`
2. Read ticket-number from the prompt.
3. Read status.json to get the ticket's status.
4. Read DESIGN.md to get the design context.
5. Read REQUIREMENT.md (if it exists) to get the requirement.

## Execution Rules

Work through the following steps in order:

### Step 1: Update Status

Update status.json: set `planner.status` to `IN_PROGRESS` and `planner.session-id` to the session-id from the prompt.

### Step 2: Generate tasks.json

Break the design down into tasks, following the principles defined in the rule files under `./rules/`. Generate tasks.json, following the shape of `${ROLE_ROOT}/tasks.template.json`: a `tasks` array, one entry per task, each with an `id`, a `description`, a `tech-stack`, and a `business-domain`.

`tech-stack` means the technical layer or stack the task belongs to (e.g. `dao`, `service`, `view`). `business-domain` means the business area or feature the task belongs to (e.g. `user`, `billing`). How tasks are split is up to the user and the rule files — there is no prescribed method.

Example:

```json
{
    "tasks": [
        {
            "id": "TASK-01",
            "description": "make user dao",
            "tech-stack": "dao",
            "business-domain": "user"
        },
        {
            "id": "TASK-02",
            "description": "make user service",
            "tech-stack": "service",
            "business-domain": "user"
        },
        {
            "id": "TASK-03",
            "description": "make user ui to call user api",
            "tech-stack": "view",
            "business-domain": "user"
        }
    ]
}
```

### Step 3: Generate TR

Generate TR. See `TASKS_REQUEST.md` for the detailed structure.

After generating TR, **do not commit**. Echo it back to the user and wait for a reply.

The user may keep asking questions or modify tasks.json directly until satisfied. If tasks.json changes, regenerate TR to match and echo again. Repeat until the user replies `approve` or `reject`.

### Step 4: Update Status

Update status.json: set `planner.status` to `WAITING`.

## TR Reply Handling

After TR is created, wait for the user's reply and act as follows:

- **approve**:
  1. For each `<rule file>: <rule text>` line in the **New Rules** section of TR, append `<rule text>` to `${ROLE_ROOT}/<rule file>` (create the file if it does not exist)
  2. Delete TR
  3. Commit tasks.json
  4. Set `planner.status` in status.json to `DONE`

- **reject**:
  1. Delete tasks.json
  2. Delete TR
  3. Set `planner.status` in status.json to `TODO`

- **Any other reply (ask, modify, etc.)**: do not modify TR or status.json
