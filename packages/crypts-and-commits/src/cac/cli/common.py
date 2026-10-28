import sys
from functools import wraps
from typing import NoReturn

import click
import typer
from rich.console import Console

from cac.core import references
from cac.core.recovery import RecoveryError


def reference_inputs(domain: str, **options):
    """Adapt CLI inputs through the shared core boundary and render its errors literally."""

    def decorate(function):
        def report(identity):
            Console().print("identity: " + references.encoded(identity), markup=False, highlight=False, soft_wrap=True)

        adapted = references.inputs(domain, reporter=report, **options)(function)

        @wraps(function)
        def invoke(*args, **kwargs):
            try:
                return adapted(*args, **kwargs)
            except (ValueError, OSError, RecoveryError) as exc:
                Console().print(str(exc), markup=False)
                raise typer.Exit(code=1) from exc

        invoke.reference_contract = adapted.reference_contract
        invoke.__doc__ = adapted.__doc__
        return invoke

    return decorate


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


def resolve_body_input(body: str | None, body_file: str | None) -> str | None:
    """Resolve explicit CLI input, preserving None for the command's editor fallback."""
    if body is not None and body_file is not None:
        raise typer.BadParameter("--body and --body-file cannot be used together.", param_hint="--body-file")
    if body_file is None:
        return body
    try:
        with open(body_file, encoding="utf-8", newline="") as source:
            return source.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise typer.BadParameter(f"Cannot read UTF-8 body file {body_file!r}: {exc}", param_hint="--body-file") from exc


CURSOR_HELP = "Continue a truncated body from a previous page's next_cursor."


def fitted(console: Console, build):
    """Run a core get fit, rendering cursor/budget errors literally."""
    try:
        return build()
    except ValueError as exc:
        console.print(str(exc), markup=False)
        raise typer.Exit(code=1) from exc


def print_body(console: Console, response: dict) -> None:
    """Print a fitted body; a truncated page ends with its notice and continuation cursor."""
    console.print(response["body"], markup=False, soft_wrap=True)
    if response.get("next_cursor"):
        console.print()
        console.print(response["notice"], markup=False, soft_wrap=True)
        console.print(f"next_cursor: {response['next_cursor']}", markup=False, soft_wrap=True)


def fail(console: Console, message: str) -> NoReturn:
    console.print(f"[bold red]{message}[/bold red]")
    raise typer.Exit(code=1)
