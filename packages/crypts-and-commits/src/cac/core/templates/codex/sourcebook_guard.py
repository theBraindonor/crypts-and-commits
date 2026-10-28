"""Deny apply_patch file targets inside CAC's managed sourcebook directory."""

from __future__ import annotations

import json
import ntpath
import os
import posixpath
import sys

TARGET_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")


def _protected_target(path: str) -> bool:
    """Check lexical path components; this is not a symlink-aware filesystem sandbox."""
    windows_path = os.name == "nt" or bool(ntpath.splitdrive(path)[0]) or "\\" in path
    normalized = posixpath.normpath(path.replace("\\", "/"))
    parts = normalized.split("/")
    if windows_path:
        parts = [part.casefold() for part in parts]
    return ".sourcebook" in parts


def _patch_targets(patch: str) -> list[str]:
    # Patch body lines start with a space, +, or -, so header-like content
    # cannot be confused with the unprefixed file-operation headers.
    return [
        line[len(header) :].strip()
        for line in patch.split("\n")
        for header in TARGET_HEADERS
        if line.startswith(header)
    ]


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
    try:
        event = json.load(sys.stdin)
    except (ValueError, UnicodeDecodeError):
        return
    if not isinstance(event, dict) or event.get("tool_name") != "apply_patch":
        return
    tool_input = event.get("tool_input")
    patch = tool_input.get("command") if isinstance(tool_input, dict) else tool_input
    if not isinstance(patch, str):
        return

    if any(_protected_target(target) for target in _patch_targets(patch)):
        _deny(
            ".sourcebook is managed only through the crypts-and-commits MCP server "
            "or the cac CLI fallback. Direct apply_patch edits are blocked."
        )


if __name__ == "__main__":
    main()
