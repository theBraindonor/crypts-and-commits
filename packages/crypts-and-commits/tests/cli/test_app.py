from typer.testing import CliRunner

from cac.cli.app import app

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
