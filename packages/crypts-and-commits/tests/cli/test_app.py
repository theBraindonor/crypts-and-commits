import re

import pytest
from cac.cli.app import app
from typer.main import get_command
from typer.testing import CliRunner

runner = CliRunner()


def test_help_shows_description() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Crypts and Commits CLI." in result.output


def test_no_args_requires_a_command() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 2


def test_help_lists_bootstrap_module() -> None:
    result = runner.invoke(app, ["--help"])

    assert "bootstrap" in result.output


def test_root_callback_configures_output_encoding(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[bool] = []
    monkeypatch.setattr("cac.cli.app.configure_output_encoding", lambda: calls.append(True))
    monkeypatch.chdir(tmp_path)

    # Any real subcommand runs the root callback first, even when the command
    # itself then fails (no sourcebook here). --help would short-circuit before
    # the callback, so invoke an actual command instead.
    runner.invoke(app, ["world", "get"])

    assert calls == [True]


def _leaf_commands(command, path=()):
    if hasattr(command, "commands"):
        for name, child in command.commands.items():
            yield from _leaf_commands(child, (*path, name))
    else:
        yield " ".join(path), command


def test_every_command_help_is_clean_prose() -> None:
    """Undecorated help relies on Typer/click docstring cleaning; decorated help on references.inputs.
    Walking every leaf command verifies both."""
    commands = list(_leaf_commands(get_command(app)))
    assert commands
    for path, command in commands:
        help_text = command.help or ""
        assert not re.search(r"\S {2,}", help_text), path
        assert not re.search(r"\n[ \t]+", help_text), path
