import pytest
from cac.cli.app import app
from cac.core import boss, config, git_utils, world
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def bootstrapped(tmp_path):
    world.initialize_world(tmp_path)


def invoke(*args):
    return runner.invoke(app, ["boss", *args])


def create(name="goal"):
    result = invoke("create", name, "--body", "[tool.ruff]", "--summary", "[summary]")
    assert result.exit_code == 0, result.output


def test_all_commands_and_lifecycle(tmp_path):
    help_result = invoke("--help")
    assert help_result.exit_code == 0
    for command in (
        "create",
        "get",
        "list",
        "update",
        "make-available",
        "withdraw",
        "reactivate",
        "archive",
        "assign-dependency",
        "unassign-dependency",
    ):
        assert command in help_result.output
    create()
    create("other")
    for args in [
        ("make-available", "goal"),
        ("assign-dependency", "goal", "other"),
        ("unassign-dependency", "goal", "other"),
        ("update", "goal", "-b", "[bold]literal[/bold]", "-s", "[summary]"),
        ("withdraw", "goal"),
        ("reactivate", "goal"),
        ("withdraw", "goal"),
        ("archive", "goal"),
    ]:
        result = invoke(*args)
        assert result.exit_code == 0, result.output
    result = invoke("get", "goal")
    assert result.exit_code == 0
    assert "[bold]literal[/bold]" in result.output
    assert "[summary]" in result.output
    assert "goal" not in invoke("list").output
    assert "goal" in invoke("list", "--include-archived").output


@pytest.mark.parametrize("operation", ["create", "update"])
def test_body_file_and_editor(tmp_path, monkeypatch, operation):
    if operation == "update":
        create()
    source = tmp_path / "body file.md"
    source.write_bytes("[tool.pdm]\r\n\r\nCafé\r\n".encode())
    result = invoke(operation, "goal", "--body-file", str(source), "--summary", "Summary")
    assert result.exit_code == 0, result.output
    assert "Café" in boss.read_metadata(tmp_path, "goal")[1]
    initial = []
    monkeypatch.setattr("cac.cli.boss.edit_markdown", lambda body: initial.append(body) or "Editor content")
    result = invoke(operation, "edited" if operation == "create" else "goal", "-s", "Editor summary")
    assert result.exit_code == 0, result.output
    assert initial
    assert "Goal" in initial[0] if operation == "create" else "Café" in initial[0]


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize("failure", ["conflict", "missing", "directory", "invalid-utf8", "unreadable", "no-summary"])
def test_body_file_errors_before_mutation(tmp_path, monkeypatch, operation, failure):
    if operation == "update":
        create()
    before = boss.read_metadata(tmp_path, "goal") if operation == "update" else None
    source = tmp_path / "body.md"
    source.write_bytes(b"\xff" if failure == "invalid-utf8" else b"new body")
    args = [operation, "goal", "--body-file", str(source)]
    if failure != "no-summary":
        args += ["-s", "Summary"]
    if failure == "conflict":
        args += ["-b", ""]
    elif failure == "missing":
        source.unlink()
    elif failure == "directory":
        args[3] = str(tmp_path)
    elif failure == "unreadable":

        def denied(*args, **kwargs):
            raise PermissionError("denied")

        monkeypatch.setattr("cac.cli.common.open", denied, raising=False)
    result = invoke(*args)
    assert result.exit_code != 0
    if before is None:
        assert boss.list_bosses(tmp_path) == []
    else:
        assert boss.read_metadata(tmp_path, "goal") == before


def test_errors_and_budget(tmp_path, monkeypatch):
    assert invoke("get", "missing").exit_code == 1
    assert invoke("get", "../bad").exit_code == 1
    create()
    assert invoke("reactivate", "goal").exit_code == 1
    assert invoke("list", "--cursor", "bad").exit_code == 1
    boss.update_boss(tmp_path, "goal", "x" * 4000, "Summary")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 500)
    assert "TRUNCATED" in invoke("get", "goal").output
    create("other")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 150)
    first = invoke("list")
    assert "goal" in first.output and "Next cursor: 1" in first.output
    second = invoke("list", "--cursor", "1")
    assert "other" in second.output and "goal" not in second.output


def test_missing_git_identity_is_a_readable_cli_error(tmp_path, monkeypatch):
    create()
    path = boss.boss_path(tmp_path, "goal")
    before = path.read_bytes()

    def denied(root):
        raise git_utils.GitIdentityError("[identity] not configured")

    monkeypatch.setattr(git_utils, "current_git_user", denied)
    result = invoke("withdraw", "goal")
    assert result.exit_code == 1
    assert "[identity] not configured" in result.output
    assert path.read_bytes() == before
