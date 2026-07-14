import argparse
import sys
from pathlib import Path


def echo_cr(ticket_number: str) -> None:
    cr_path = Path("plato-workspace/tickets") / ticket_number / ".cr.md"
    if not cr_path.exists():
        print(f".cr.md not found for ticket {ticket_number}", file=sys.stderr)
        sys.exit(1)
    print(cr_path.read_text(encoding="utf-8"))


def echo_task_approve(ticket_number: str) -> None:
    print(
        f"Done. Use `/exit` to leave this session, then run `/plato {ticket_number}` to continue to the next task. "
        "**The framework does not commit or push — remember to do it manually.**"
    )


def echo_task_reject(ticket_number: str) -> None:
    print(
        f"Change rejected. Use `/exit` to leave this session, then run `/plato {ticket_number}` to start this task over."
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(prog="echo_cli.py", description="Echo plato files to the user")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cr_parser = subparsers.add_parser("cr", help="print the ticket's .cr.md")
    cr_parser.add_argument("ticket_number")

    task_parser = subparsers.add_parser("task", help="task-related echo messages")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)

    approve_parser = task_subparsers.add_parser("approve", help="print the message shown after a task is approved")
    approve_parser.add_argument("ticket_number")

    reject_parser = task_subparsers.add_parser("reject", help="print the message shown after a task is rejected")
    reject_parser.add_argument("ticket_number")

    args = parser.parse_args()

    if args.command == "cr":
        echo_cr(args.ticket_number)
    elif args.command == "task" and args.task_command == "approve":
        echo_task_approve(args.ticket_number)
    elif args.command == "task" and args.task_command == "reject":
        echo_task_reject(args.ticket_number)


if __name__ == "__main__":
    main()
