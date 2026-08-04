import json
import logging
import os

logger = logging.getLogger(__name__)


def save_json(path: str, data) -> None:
    """Write data as JSON to path, creating the parent dir if needed."""
    parent_dir = os.path.dirname(path) or "."
    os.makedirs(parent_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_json(path: str, default):
    """Read JSON from path; return default if the file is missing or on read error."""
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.error("Failed to read %s: %s", path, exc)
        return default
