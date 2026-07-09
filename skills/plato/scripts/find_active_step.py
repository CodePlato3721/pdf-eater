import json
import sys
from pathlib import Path


def load_plan_tasks(ticket_number: str) -> list:
    tasks_path = Path("plato-workspace/tickets") / ticket_number / "tasks.json"
    if not tasks_path.exists():
        return []

    plan = json.loads(tasks_path.read_text(encoding="utf-8"))
    return plan.get("tasks", [])


def find_active_coder_task(coder: dict, ticket_number: str, status_path: Path, status: dict):
    tasks = coder.get("tasks", [])

    # 1. The last non-DONE record already tracked in status.json.
    active_task = next((t for t in reversed(tasks) if t.get("status") != "DONE"), None)
    if active_task is not None:
        return active_task

    # 2. Everything tracked so far is DONE (or nothing is tracked yet) — pull
    # the next not-yet-tracked task from tasks.json. Only one task is ever
    # appended at a time, so edits to tasks.json made while earlier tasks are
    # still in flight are picked up as we go instead of being locked in by an
    # upfront bootstrap.
    known_ids = {t.get("id") for t in tasks}
    next_plan_task = next((pt for pt in load_plan_tasks(ticket_number) if pt.get("id") not in known_ids), None)
    if next_plan_task is None:
        return None

    new_task = {"id": next_plan_task["id"], "status": "TODO", "coder": {"session-id": ""}}
    tasks.append(new_task)
    coder["tasks"] = tasks
    status["coder"] = coder
    status_path.write_text(json.dumps(status, indent=4), encoding="utf-8")
    return new_task


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: find_active_step.py <ticket-number>", file=sys.stderr)
        sys.exit(1)

    ticket_number = sys.argv[1]
    status_path = Path("plato-workspace/tickets") / ticket_number / "status.json"

    if not status_path.exists():
        print(f"status.json not found for ticket {ticket_number}", file=sys.stderr)
        sys.exit(1)

    status = json.loads(status_path.read_text(encoding="utf-8"))

    designer = status.get("designer", {})
    if designer.get("status") != "DONE":
        report(role="designer", status=designer.get("status", "TODO"), session_id=designer.get("session-id", ""))
        return

    planner = status.get("planner", {})
    if planner.get("status") != "DONE":
        report(role="planner", status=planner.get("status", "TODO"), session_id=planner.get("session-id", ""))
        return

    coder = status.get("coder", {})
    if coder.get("status") != "DONE":
        active_task = find_active_coder_task(coder, ticket_number, status_path, status)
        if active_task is not None:
            report(
                role="coder",
                status=active_task.get("status", "TODO"),
                session_id=active_task.get("coder", {}).get("session-id", ""),
                task_id=active_task.get("id", ""),
            )
            return

        # all tracked tasks are DONE and tasks.json has nothing new, but
        # coder.status was never flipped to DONE
        report(role="coder", status=coder.get("status", "TODO"), session_id="", task_id="")
        return

    report(role="none", status="DONE", session_id="")


def report(role: str, status: str, session_id: str, task_id: str = "") -> None:
    print(f"role: {role}")
    print(f"task-id: {task_id}")
    print(f"status: {status}")
    print(f"session-id: {session_id}")


if __name__ == "__main__":
    main()
