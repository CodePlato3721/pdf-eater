import json
from pathlib import Path


class TicketStatus:
    def __init__(self, ticket_number: str):
        self.ticket_number = ticket_number
        self._path = Path("plato-workspace/tickets") / ticket_number / "status.json"

    def exists(self) -> bool:
        return self._path.exists()

    def read(self) -> dict:
        raw = json.loads(self._path.read_text(encoding="utf-8"))
        tasks = raw.get("coder", {}).get("tasks", [])
        return {
            "ticket_number": self.ticket_number,
            "title": raw.get("title", ""),
            "designer": raw.get("designer", {}).get("status", ""),
            "planner": raw.get("planner", {}).get("status", ""),
            "coder": raw.get("coder", {}).get("status", ""),
            "tasks": [{"id": t.get("id", ""), "status": t.get("status", "")} for t in tasks],
        }
