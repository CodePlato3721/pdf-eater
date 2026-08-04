"""
Unit tests for backend/utils/file_utils.py

Run from backend/:
    .venv\\Scripts\\python.exe -m pytest tests/unit/test_file_utils.py -v
"""
import json

from utils.file_utils import load_json, save_json


class TestSaveJson:
    """Tests for save_json()"""

    def test_save_json_writes_data_and_creates_parent_dir(self, tmp_path):
        """save_json() writes data as JSON, creating the parent dir if needed."""
        target = tmp_path / "data" / "thing.json"

        save_json(str(target), {"a": 1})

        assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}

    def test_save_json_replaces_not_appends_previous_contents(self, tmp_path):
        """save_json() fully replaces the file's previous contents rather than appending."""
        target = tmp_path / "thing.json"

        save_json(str(target), ["a"])
        save_json(str(target), ["b"])

        assert json.loads(target.read_text(encoding="utf-8")) == ["b"]

    def test_save_json_writes_to_current_dir_when_path_has_no_directory(self, tmp_path, monkeypatch):
        """save_json() writes correctly when path has no directory component."""
        monkeypatch.chdir(tmp_path)

        save_json("bare.json", {"a": 1})

        assert json.loads((tmp_path / "bare.json").read_text(encoding="utf-8")) == {"a": 1}


class TestLoadJson:
    """Tests for load_json()"""

    def test_load_json_returns_parsed_data_when_file_exists(self, tmp_path):
        """load_json() returns the parsed JSON content when the file exists."""
        target = tmp_path / "thing.json"
        target.write_text(json.dumps({"a": 1}), encoding="utf-8")

        assert load_json(str(target), None) == {"a": 1}

    def test_load_json_returns_default_when_file_missing(self, tmp_path):
        """load_json() returns default without error and without creating the file
        when it doesn't exist."""
        target = tmp_path / "thing.json"

        result = load_json(str(target), [])

        assert result == []
        assert not target.exists()

    def test_load_json_returns_default_on_corrupt_file(self, tmp_path):
        """load_json() returns default instead of raising on invalid JSON."""
        target = tmp_path / "thing.json"
        target.write_text("{not valid json", encoding="utf-8")

        assert load_json(str(target), []) == []
