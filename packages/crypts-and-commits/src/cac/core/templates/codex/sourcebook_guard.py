"""Block direct Codex filesystem access to CAC's managed sourcebook."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

SOURCEBOOK_REFERENCE = re.compile(r"(?i)(?<![\w.-])\.sourcebook(?:[\\/]|$)")


def _deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main() -> None:
    event: dict[str, Any] = json.load(sys.stdin)
    tool_name = event.get("tool_name")
    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command", "")

    if tool_name in {"Bash", "apply_patch"} and SOURCEBOOK_REFERENCE.search(command):
        _deny(
            ".sourcebook is managed only through the crypts-and-commits MCP server "
            "or the cac CLI fallback. Direct filesystem access is blocked."
        )


if __name__ == "__main__":
    main()
