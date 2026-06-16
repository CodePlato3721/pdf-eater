#!/usr/bin/env python3
"""
PreToolUse hook on Bash/PowerShell.
Blocks git commit when staged changes include non-management files
but no corresponding CR archive (cr/cr.<timestamp>.md) in the staged set.
Exit code 2 blocks the tool call; stderr is shown to Claude and the user.
"""
import sys
import json
import re
import subprocess

MANAGEMENT_PREFIXES = (
    'CLAUDE.md',
    'PROJECT.md',
    'CR.md',
    'TASKS.md',
    'CODER.md',
    'PLAN.md',
    'STANDARDS.md',
    'ARCHITECTURE.md',
    'cr/',
    'scripts/',
    '.gitignore',
)


def is_management_file(path: str) -> bool:
    return any(path == p or path.startswith(p) for p in MANAGEMENT_PREFIXES)


def is_git_commit(command: str) -> bool:
    return bool(re.search(r'\bgit\s+commit\b', command))


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        capture_output=True, text=True,
    )
    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if data.get("tool_name") not in ("Bash", "PowerShell"):
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    if not is_git_commit(command):
        sys.exit(0)

    staged = get_staged_files()
    non_management = [f for f in staged if not is_management_file(f)]

    if not non_management:
        sys.exit(0)

    has_cr_archive = any(re.match(r'cr/cr\.\d{14}\.md$', f) for f in staged)
    if has_cr_archive:
        sys.exit(0)

    files_preview = ', '.join(non_management[:5])
    if len(non_management) > 5:
        files_preview += f' … 共 {len(non_management)} 个'

    print(
        f"[CR Guard] 暂存区包含非项目管理文件的改动，但未找到对应的 CR 归档文件。\n"
        f"请先生成 .cr.md，经过 approve → 归档流程后再 commit。\n"
        f"涉及文件：{files_preview}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
