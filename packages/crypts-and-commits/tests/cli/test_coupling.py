import pytest
from cac.cli.app import app
from cac.core import boss, campaign, world
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(autouse=True)
def seed(tmp_path):
    world.initialize_world(tmp_path)
    boss.create_boss(tmp_path, "b001-goal", "Aspirational body", "Summary")
    boss.make_available(tmp_path, "b001-goal")


def invoke(*args):
    return runner.invoke(app, list(args))


@pytest.mark.parametrize("input_mode", ["inline", "file", "editor"])
def test_assignment_body_input_and_reactivation(tmp_path, monkeypatch, input_mode):
    args = ["boss", "assign-campaign", "b001", "c001-work"]
    body = "[tool.ruff]\r\n\r\nTactical café\r\n"
    if input_mode == "inline":
        args += ["--body", body]
    elif input_mode == "file":
        source = tmp_path / "campaign plan.md"
        source.write_bytes(body.encode())
        args += ["--body-file", str(source)]
    else:

        def edit(initial):
            assert initial == campaign.template_body()
            assert initial != "Aspirational body"
            return body

        monkeypatch.setattr("cac.cli.boss.edit_markdown", edit)
    result = invoke(*args)
    assert result.exit_code == 0, result.output
    assert '"campaign":"c001-work"' in result.output
    assert "Tactical café" in campaign.read_campaign(tmp_path, "c001-work").body
    for args in [
        ("campaign", "open", "c001"),
        ("campaign", "complete", "c001", "-m", "Done"),
        ("campaign", "reactivate", "c001", "-m", "[feedback]"),
    ]:
        result = invoke(*args)
        assert result.exit_code == 0, result.output
    assert "[feedback]" in campaign.read_campaign(tmp_path, "c001-work").body
    inspected = invoke("campaign", "get", "c001")
    assert '"kind":"current"' in inspected.output
    denied = invoke("campaign", "delete", "c001", "--yes")
    assert denied.exit_code == 1 and "protect" in denied.output


@pytest.mark.parametrize("failure", ["both", "missing", "directory", "encoding", "unreadable"])
def test_body_input_failures_do_not_assign(tmp_path, monkeypatch, failure):
    source = tmp_path / "body.md"
    if failure == "directory":
        source.mkdir()
    elif failure != "missing":
        source.write_bytes(b"\xff" if failure == "encoding" else b"Tactical")
    if failure == "unreadable":

        def denied(*args, **kwargs):
            raise PermissionError("Read denied")

        monkeypatch.setattr("cac.cli.common.open", denied, raising=False)
    before = boss.boss_path(tmp_path, "b001-goal").read_bytes()
    args = ["boss", "assign-campaign", "b001", "c001-work", "--body-file", str(source)]
    if failure == "both":
        args += ["--body", ""]
    result = invoke(*args)
    assert result.exit_code == 2, result.output
    assert "--body-file" in result.output
    assert boss.boss_path(tmp_path, "b001-goal").read_bytes() == before
    assert not campaign.exists(tmp_path, "c001-work")


def test_reactivation_requires_reason():
    result = invoke("campaign", "reactivate", "c001")
    assert result.exit_code != 0
    assert "--message" in result.output


def test_assignment_retry_on_legacy_campaign_without_status(tmp_path):
    import frontmatter

    assert invoke("boss", "assign-campaign", "b001", "c001-work", "--body", "Plan").exit_code == 0
    path = campaign.campaign_path(tmp_path, "c001-work")
    post = frontmatter.load(path)
    post.metadata.pop("status")
    path.write_text(frontmatter.dumps(post), encoding="utf-8")
    result = invoke("boss", "assign-campaign", "b001", "c001-work", "--body", "Retry")
    assert result.exit_code == 0, result.output
    assert '"reused":true' in result.output and '"status":"draft"' in result.output
