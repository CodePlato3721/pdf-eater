import json
import sys
from pathlib import Path

ROLE_FILE = {
    "designer": "plato-roles/designer/DESIGNER.md",
    "planner": "plato-roles/planner/PLANNER.md",
    "coder": "plato-roles/coder/CODER.md",
}


def gen_session_id() -> str:
    import uuid

    return str(uuid.uuid4())


def persist_session_id(ticket_number: str, role: str, task_id: str, session_id: str) -> None:
    status_path = Path("plato-workspace/tickets") / ticket_number / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))

    if role == "coder":
        for task in status.get("coder", {}).get("tasks", []):
            if task.get("id") == task_id:
                task.setdefault("coder", {})["session-id"] = session_id
                break
    else:
        status.setdefault(role, {})["session-id"] = session_id

    status_path.write_text(json.dumps(status, indent=4), encoding="utf-8")


def main() -> None:
    if len(sys.argv) not in (5, 6):
        print(
            "usage: generate_command.py <ticket-number> <role> <status> <session-id> [task-id]",
            file=sys.stderr,
        )
        sys.exit(1)

    ticket_number, role, status, session_id = sys.argv[1:5]
    task_id = sys.argv[5] if len(sys.argv) == 6 else ""

    if status == "TODO":
        if not session_id:
            session_id = gen_session_id()
            persist_session_id(ticket_number, role, task_id, session_id)

        role_file = ROLE_FILE[role]
        print("You can start this step now:")
        print()
        print(f'    claude -p --session-id "{session_id}" --append-system-prompt-file "{role_file}"')
        return

    if status == "IN_PROGRESS":
        print(f"The {role} agent is currently running in the background. Please wait -")
        print("once it finishes you can resume the session with:")
        print()
        print(f'    claude --resume "{session_id}"')
        return

    if status == "WAITING":
        print(f"The {role} agent finished its run and is waiting for your input.")
        print("Resume the session with:")
        print()
        print(f'    claude --resume "{session_id}"')
        return

    print(f"unexpected status: {status}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
