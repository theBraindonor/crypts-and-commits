import sys
from typing import NoReturn

import click
import typer
from rich.console import Console


def configure_output_encoding() -> None:
    """Force UTF-8 on the process stdout/stderr streams.

    On Windows the interpreter's stdout/stderr default to the legacy code page
    (cp1252), so ``rich`` fails with ``UnicodeEncodeError`` when printing stored
    content that contains characters outside that page (arrows, dashes, smart
    quotes, ...). Reconfiguring the streams to UTF-8 makes correct display
    independent of the caller's environment.

    Streams that do not support ``reconfigure`` (e.g. test-capture buffers or
    some redirected streams that are not ``TextIOWrapper``) are left untouched.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="backslashreplace")


def edit_markdown(initial: str) -> str:
    edited = click.edit(initial, extension=".txt")
    return edited if edited is not None else initial


def fail(console: Console, message: str) -> NoReturn:
    console.print(f"[bold red]{message}[/bold red]")
    raise typer.Exit(code=1)
