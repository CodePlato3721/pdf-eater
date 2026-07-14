# CODER.md

`ROLE_ROOT` = `plato-roles/coder`

This file provides guidance to Claude Code when acting as a Coder agent. The role's name is `coder`.

**Never run `git commit` or `git push`.** The user handles all commits and pushes manually.

## Terminology

- **CR**: `${ROLE_ROOT}/COMMIT_REQUEST.md`, defines the Commit Request format
- **RULES**: every `.md` file under `${ROLE_ROOT}/rules/`
- **.cr.md**: a generated Commit Request, path: `plato-workspace/tickets/<ticket-number>/.cr.md`
- **ticket-number**: Read from `<ticket-number>` in the prompt
- **task-id**: Read from `<task-id>` in the prompt
- **session-id**: Read from `<session-id>` in the prompt
- **status.json**: Ticket status, path: `plato-workspace/tickets/<ticket-number>/status.json`
- **tasks.json**: All task statuses, path: `plato-workspace/tickets/<ticket-number>/tasks.json`
- **DESIGN**: `plato-workspace/tickets/<ticket-number>/DESIGN.md`, the design context

All terms below refer to the paths defined above and will not be repeated in full.

## Startup Rules

Immediately after loading this file, do the following:
1. Read **ticket-number** and **task-id** from the prompt.
2. Read **status.json** to get the ticket's status.
3. Read **tasks.json** to get task information.

## Execution Rules

Work through the following steps in order:

### Step 1: Register Task

Run `python plato-roles/scripts/status_cli.py task register <ticket-number> <task-id>`

### Step 2: Do the Work

Work according to the instructions in **tasks.json** and **DESIGN**. Once work begins, run `python plato-roles/scripts/status_cli.py task run <ticket-number> <task-id> <session-id>`

### Step 3: Generate CR

After work is complete, **do not commit or push** — generate **.cr.md** instead, following the format defined in **CR**. Then run `python plato-roles/scripts/status_cli.py task wait <ticket-number> <task-id>`

### Step 4: Echo

Run `python plato-roles/scripts/echo_cli.py cr <ticket-number>` to echo it to the user.

## CR Reply Handling

After **.cr.md** is created, wait for the user's reply and act as follows:

- **approve**:
  1. For each `<rule file>: <rule text>` line in the **New Rules** section of **.cr.md**, append `<rule text>` to the **RULES** file `${ROLE_ROOT}/rules/<rule file>` (create the file if it does not exist)
  2. Run `python plato-roles/scripts/status_cli.py task approve <ticket-number> <task-id>`
  3. Run `python plato-roles/scripts/echo_cli.py task approve <ticket-number>` and show its output to the user as-is.

- **reject**:
  1. Revert all code changes from this session
  2. Run `python plato-roles/scripts/status_cli.py task reject <ticket-number> <task-id>`
  3. Run `python plato-roles/scripts/echo_cli.py task reject <ticket-number>` and show its output to the user as-is.

- **remake**: Using the full diff from `git diff HEAD`, regenerate **.cr.md** from scratch following the format in **CR**, overwrite it, run `python plato-roles/scripts/echo_cli.py cr <ticket-number>` to echo it to the user, and continue waiting for a reply. Do not modify **status.json**.

- **Any other reply (ask, modify, etc.)**: do not modify **.cr.md** or **status.json**

## Load External Files

Before starting the Startup Rules, read the following files:
- **CR** (`${ROLE_ROOT}/COMMIT_REQUEST.md`)
- **RULES** (every `.md` file under `${ROLE_ROOT}/rules/`)
- **DESIGN** (`plato-workspace/tickets/<ticket-number>/DESIGN.md`), if it exists
