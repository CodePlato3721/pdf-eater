# Creation Flow

1. Ask the ticket type. Use `AskUserQuestion` with two options: `feature` and
   `defect`.
2. Ask the ticket title (free text): "What is the title of this ticket?"
3. Create `plato-workspace/tickets/<ticket-number>/` if it doesn't exist, and
   copy `skills/plato/references/status.default.json` into it as `status.json`.
4. Edit the new `status.json`:
   - set `type` to the chosen type
   - set `title` to the given title
5. Run `python skills/plato/scripts/generate_command.py <ticket-number> designer TODO ""` —
   the script will generate a new session-id automatically.
6. Tell the user the ticket workspace was created, and show the script's output as-is.
