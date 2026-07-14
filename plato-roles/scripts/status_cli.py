import argparse
import json
import sys
from pathlib import Path


def status_path(ticket_number: str) -> Path:
    return Path("plato-workspace/tickets") / ticket_number / "status.json"


def load_status(ticket_number: str) -> tuple[Path, dict]:
    path = status_path(ticket_number)
    if not path.exists():
        print(f"status.json not found for ticket {ticket_number}", file=sys.stderr)
        sys.exit(1)
    return path, json.loads(path.read_text(encoding="utf-8"))


def save_status(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def task_register(ticket_number: str, task_id: str) -> None:
    path, data = load_status(ticket_number)
    tasks = data.setdefault("coder", {}).setdefault("tasks", [])

    if any(t.get("id") == task_id for t in tasks):
        print(f"{task_id} is already registered in ticket {ticket_number}")
        return

    tasks.append({"id": task_id, "status": "TODO", "coder": {"session-id": ""}})
    save_status(path, data)
    print(f"registered {task_id} in ticket {ticket_number}")


def set_task_status(ticket_number: str, task_id: str, status: str, session_id: str | None = None) -> None:
    path, data = load_status(ticket_number)
    tasks = data.get("coder", {}).get("tasks", [])

    for task in tasks:
        if task.get("id") == task_id:
            task["status"] = status
            if session_id is not None:
                task.setdefault("coder", {})["session-id"] = session_id
            save_status(path, data)
            print(f"{task_id} in ticket {ticket_number} set to {status}")
            return

    print(f"{task_id} not found in ticket {ticket_number} - register it first", file=sys.stderr)
    sys.exit(1)


def task_run(ticket_number: str, task_id: str, session_id: str) -> None:
    set_task_status(ticket_number, task_id, "IN_PROGRESS", session_id)


def task_wait(ticket_number: str, task_id: str) -> None:
    set_task_status(ticket_number, task_id, "WAITING")


def delete_cr(ticket_number: str) -> None:
    cr_path = Path("plato-workspace/tickets") / ticket_number / ".cr.md"
    if cr_path.exists():
        cr_path.unlink()
        print(f"deleted {cr_path.as_posix()}")


def task_approve(ticket_number: str, task_id: str) -> None:
    delete_cr(ticket_number)
    set_task_status(ticket_number, task_id, "DONE")


def task_reject(ticket_number: str, task_id: str) -> None:
    delete_cr(ticket_number)
    set_task_status(ticket_number, task_id, "TODO", session_id="")


def main() -> None:
    parser = argparse.ArgumentParser(prog="status_cli.py", description="Manage status.json for a ticket")
    subparsers = parser.add_subparsers(dest="command", required=True)

    task_parser = subparsers.add_parser("task", help="task-related commands")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)

    register_parser = task_subparsers.add_parser("register", help="register a task in coder.tasks if not present")
    register_parser.add_argument("ticket_number")
    register_parser.add_argument("task_id")

    run_parser = task_subparsers.add_parser("run", help="set a task's status to IN_PROGRESS and record its session-id")
    run_parser.add_argument("ticket_number")
    run_parser.add_argument("task_id")
    run_parser.add_argument("session_id")

    wait_parser = task_subparsers.add_parser("wait", help="set a task's status to WAITING")
    wait_parser.add_argument("ticket_number")
    wait_parser.add_argument("task_id")

    approve_parser = task_subparsers.add_parser("approve", help="delete .cr.md and set a task's status to DONE")
    approve_parser.add_argument("ticket_number")
    approve_parser.add_argument("task_id")

    reject_parser = task_subparsers.add_parser(
        "reject", help="delete .cr.md, set a task's status back to TODO and clear its session-id"
    )
    reject_parser.add_argument("ticket_number")
    reject_parser.add_argument("task_id")

    args = parser.parse_args()

    if args.command == "task" and args.task_command == "register":
        task_register(args.ticket_number, args.task_id)
    elif args.command == "task" and args.task_command == "run":
        task_run(args.ticket_number, args.task_id, args.session_id)
    elif args.command == "task" and args.task_command == "wait":
        task_wait(args.ticket_number, args.task_id)
    elif args.command == "task" and args.task_command == "approve":
        task_approve(args.ticket_number, args.task_id)
    elif args.command == "task" and args.task_command == "reject":
        task_reject(args.ticket_number, args.task_id)


if __name__ == "__main__":
    main()
