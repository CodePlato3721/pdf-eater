# Feature Creation Flow

Reached when the ticket type (already determined by the entry point) is `feature`.

1. Ask the ticket title (free text): "What is the title of this ticket?"
2. Infer a default `unit-test-path` by inspecting the project structure (look for
   directories named `tests/unit`, `test/unit`, `backend/tests/unit`, etc.). Use the
   first match, or fall back to `tests/unit` if none is found. Ask the user using
   `AskUserQuestion`:
   - Option A: the inferred default (label it as "Use default: <path>")
   - Option B: "Enter a custom path" (user types their own value)
3. Infer a default `e2e-test-path` the same way (look for `tests/e2e`, `test/e2e`,
   `backend/tests/e2e`, etc.; fall back to `tests/e2e`). Ask the user using
   `AskUserQuestion` in the same way as step 2.
4. Create `plato-workspace/tickets/<ticket-number>/` if it doesn't exist, and
   copy `skills/plato/references/status.default.feature.json` into it as `status.json`.
5. Edit the new `status.json`:
   - set `type` to `feature`
   - set `title` to the given title
   - set `unit-test-path` to the value confirmed in step 2
   - set `e2e-test-path` to the value confirmed in step 3
6. Run `python skills/plato/scripts/generate_command.py <ticket-number> designer TODO ""` —
   the script will generate a new session-id automatically.
7. Create `plato-workspace/tickets/<ticket-number>/REQUIREMENT.md` initialized with exactly these two empty sections:
   ```
   # User Story

   # Acceptance Criteria

   ```
8. Tell the user:
   - The ticket workspace was created.
   - Show the script's output from step 6 as-is.
   - "Please fill in your requirements in `plato-workspace/tickets/<ticket-number>/REQUIREMENT.md` before starting the designer step."
