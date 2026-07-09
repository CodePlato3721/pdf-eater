import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: status_report.py <ticket-number>", file=sys.stderr)
        sys.exit(1)

    ticket_number = sys.argv[1]
    status_path = Path("plato-workspace/tickets") / ticket_number / "status.json"

    if not status_path.exists():
        print(f"status.json not found for ticket {ticket_number}", file=sys.stderr)
        sys.exit(1)

    status = json.loads(status_path.read_text(encoding="utf-8"))

    lines = [
        f"ticket number: {ticket_number}",
        f"title: {status.get('title', '')}",
        f"designer: {status.get('designer', {}).get('status', '')}",
        f"planner: {status.get('planner', {}).get('status', '')}",
        f"coder: {status.get('coder', {}).get('status', '')}",
        "tasks:",
    ]

    tasks = status.get("coder", {}).get("tasks", [])
    if tasks:
        for task in tasks:
            lines.append(f"{task.get('id', '')}: {task.get('status', '')}")
    else:
        lines.append("(none yet)")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
