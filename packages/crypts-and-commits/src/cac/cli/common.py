from typing import NoReturn

import click
import typer
from rich.console import Console


def edit_markdown(initial: str) -> str:
    edited = click.edit(initial, extension=".txt")
    return edited if edited is not None else initial


def fail(console: Console, message: str) -> NoReturn:
    console.print(f"[bold red]{message}[/bold red]")
    raise typer.Exit(code=1)
