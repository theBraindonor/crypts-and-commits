import io
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
import typer
from cac.cli import common as cli_common
from cac.cli.app import app
from cac.cli.common import configure_output_encoding, resolve_body_input
from cac.core import boss, campaign, encounter, lore, region, world
from typer.testing import CliRunner

runner = CliRunner()


@pytest.fixture(
    params=[
        ("world", "set-body"),
        *[(d, op) for d in ("lore", "region", "campaign", "encounter", "boss") for op in ("create", "update")],
    ]
)
def body_command(
    request: pytest.FixtureRequest, tmp_path: Path, seed_world: Callable[[], None]
) -> tuple[list[str], Callable[[], str], str]:
    domain, operation = request.param
    module = {
        "world": world,
        "lore": lore,
        "region": region,
        "campaign": campaign,
        "encounter": encounter,
        "boss": boss,
    }[domain]
    args = [domain, operation]
    if domain == "world":
        seed_world()
        reader = lambda: world.read_world(tmp_path).body
    else:
        args.append("file-input")
        if domain in ("lore", "region", "boss"):
            args.extend(["--summary", "Summary."])
        if domain == "encounter":
            campaign.create_campaign(tmp_path, "opening-gambit", "Campaign.")
            campaign.open_campaign(tmp_path, "opening-gambit")
            reader = lambda: encounter.read_encounter(tmp_path, "opening-gambit", "file-input").body
        elif domain == "boss":
            seed_world()
            reader = lambda: boss.read_metadata(tmp_path, "file-input")[1]
        else:
            read = getattr(module, f"read_{domain}")
            reader = lambda: read(tmp_path, "file-input").body
        if operation == "update":
            created = runner.invoke(app, [domain, "create", *args[2:], "--body", "Original body."])
            assert created.exit_code == 0, created.output
    initial = module.template_body() if operation == "create" else reader()
    return args, reader, initial


def _markdown_snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*.md") if path.is_file()}


@pytest.mark.parametrize(
    "text", ["", "first\nsecond\n", "first\r\nsecond\r\n", "Unicode: café → [tool.pdm.workspace]\n"]
)
def test_resolve_body_file_preserves_utf8_and_newlines(tmp_path: Path, text: str) -> None:
    source = tmp_path / "body file.md"
    original = text.encode("utf-8")
    source.write_bytes(original)

    assert resolve_body_input(None, str(source)) == text
    assert source.read_bytes() == original


def test_resolve_body_input_distinguishes_empty_from_absent() -> None:
    assert resolve_body_input(None, None) is None
    assert resolve_body_input("", None) == ""
    assert resolve_body_input("inline", None) == "inline"


@pytest.mark.parametrize("body", ["", "inline"])
def test_resolve_body_input_rejects_both_options_before_reading(body: str) -> None:
    with pytest.raises(typer.BadParameter, match="cannot be used together"):
        resolve_body_input(body, "missing.md")


@pytest.mark.parametrize(
    "text",
    ["", "# Café\n\n[tool.pdm.workspace]\n[[wiki-link]]", "large markdown\n" * 10000],
    ids=["empty", "markdown", "large"],
)
def test_all_body_commands_accept_file_input(
    body_command: tuple[list[str], Callable[[], str], str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str
) -> None:
    args, reader, _ = body_command
    source = tmp_path / "body file.md"
    original = text.encode("utf-8")
    source.write_bytes(original)
    monkeypatch.setattr(cli_common.click, "edit", lambda *a, **kw: pytest.fail("Explicit input opened editor"))

    result = runner.invoke(app, [*args, "--body-file", str(source)])

    assert result.exit_code == 0, result.output
    assert reader() == text.strip()  # Existing frontmatter storage semantics.
    assert source.read_bytes() == original


@pytest.mark.parametrize("failure", ["missing", "directory", "encoding", "unreadable", "both", "both-empty"])
def test_body_file_errors_leave_records_unchanged(
    body_command: tuple[list[str], Callable[[], str], str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    args, _, _ = body_command
    source = tmp_path / "[tool.pdm.workspace] body.md"
    if failure == "directory":
        source.mkdir()
    elif failure != "missing":
        source.write_bytes(b"\xff" if failure == "encoding" else b"Body.")
    if failure == "unreadable":
        import builtins

        original_open = builtins.open

        def deny_source(file: object, *a: object, **kw: object) -> object:
            if str(file) == str(source):
                raise PermissionError("Read denied")
            return original_open(file, *a, **kw)

        monkeypatch.setattr(builtins, "open", deny_source)
    monkeypatch.setattr(cli_common.click, "edit", lambda *a, **kw: pytest.fail("File error opened editor"))
    before = _markdown_snapshot(tmp_path)
    options = ["--body-file", str(source)]
    if failure.startswith("both"):
        options.extend(["--body", "" if failure == "both-empty" else "inline"])

    result = runner.invoke(app, [*args, *options])

    assert result.exit_code == 2, result.output
    assert "--body-file" in result.output
    assert "Traceback" not in result.output
    if not failure.startswith("both"):
        assert "[tool.pdm.workspace]" in result.output
    assert _markdown_snapshot(tmp_path) == before


def test_body_commands_preserve_editor_initial_content(
    body_command: tuple[list[str], Callable[[], str], str], monkeypatch: pytest.MonkeyPatch
) -> None:
    args, reader, initial = body_command
    seen = []

    def edit(content: str, **kwargs: object) -> str:
        seen.append(content)
        return "Edited body."

    monkeypatch.setattr(cli_common.click, "edit", edit)
    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.output
    assert seen == [initial]
    assert reader() == "Edited body."


def test_body_commands_document_both_input_methods(body_command: tuple[list[str], Callable[[], str], str]) -> None:
    args, _, _ = body_command
    result = runner.invoke(app, [*args[:2], "--help"])

    assert result.exit_code == 0
    assert "--body-file" in result.output
    assert "neither body option" in result.output


def test_configure_output_encoding_switches_cp1252_stream_to_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    # A default CliRunner/StringIO capture buffer is UTF-8 and would pass even
    # with the bug present, so reproduce the real failure mode: a stream whose
    # encoding is cp1252 (the Windows legacy code page) cannot encode U+2192.
    assert "→".encode("cp1252", errors="ignore") == b""  # sanity: unencodable in cp1252

    raw = io.BytesIO()
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(raw, encoding="cp1252"))
    monkeypatch.setattr(sys, "stderr", io.TextIOWrapper(io.BytesIO(), encoding="cp1252"))

    configure_output_encoding()

    assert sys.stdout.encoding.lower() == "utf-8"
    assert sys.stderr.encoding.lower() == "utf-8"

    # The arrow that crashed `cac ... get` on Windows now round-trips.
    sys.stdout.write("→")
    sys.stdout.flush()
    assert "→".encode() in raw.getvalue()


def test_configure_output_encoding_ignores_streams_without_reconfigure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Streams that are not TextIOWrapper (e.g. test-capture buffers) have no
    # reconfigure(); the helper must skip them, not raise.
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())

    configure_output_encoding()  # must not raise


# Escaping-heavy, non-ASCII, markup-like text; ends without whitespace, which storage would strip.
CONTINUED_BODY = 'Intro "quoted" \\ back\nCafé ✓ — [tool.ruff] ' * 150 + "end."


def _continuation_domains():
    from cac.mcp import boss as boss_mcp
    from cac.mcp import campaign as campaign_mcp
    from cac.mcp import encounter as encounter_mcp
    from cac.mcp import lore as lore_mcp
    from cac.mcp import region as region_mcp
    from cac.mcp import world as world_mcp

    def encounter_setup():
        campaign_mcp.campaign_create("c001-work", "Plan")
        encounter_mcp.encounter_create("e001-task", CONTINUED_BODY, campaign="c001")
        for index in range(6):
            region_mcp.region_create(f"area-{index}-with-a-long-name", "Body", "Summary")
            encounter_mcp.encounter_assign_region("c001/e001", f"area-{index}-with-a-long-name")

    return {
        "world": (
            lambda: world_mcp.world_set_body(CONTINUED_BODY),
            lambda cursor: world_mcp.world_get(cursor=cursor),
            lambda: world_mcp.world_set_body(CONTINUED_BODY + "edit"),
            ["world", "get"],
        ),
        "lore": (
            lambda: lore_mcp.lore_create("style", CONTINUED_BODY, "Summary"),
            lambda cursor: lore_mcp.lore_get("style", cursor=cursor),
            lambda: lore_mcp.lore_update("style", CONTINUED_BODY + "edit", "Summary"),
            ["lore", "get", "style"],
        ),
        "region": (
            lambda: region_mcp.region_create("north", CONTINUED_BODY, "Summary"),
            lambda cursor: region_mcp.region_get("north", cursor=cursor),
            lambda: region_mcp.region_update("north", CONTINUED_BODY + "edit", "Summary"),
            ["region", "get", "north"],
        ),
        "campaign": (
            lambda: campaign_mcp.campaign_create("c001-work", CONTINUED_BODY),
            lambda cursor: campaign_mcp.campaign_get("c001", cursor=cursor),
            lambda: campaign_mcp.campaign_update("c001", CONTINUED_BODY + "edit"),
            ["campaign", "get", "c001"],
        ),
        "boss": (
            lambda: boss_mcp.boss_create("b001-goal", CONTINUED_BODY, "Summary"),
            lambda cursor: boss_mcp.boss_get("b001", cursor=cursor),
            lambda: boss_mcp.boss_update("b001", CONTINUED_BODY + "edit", "Summary"),
            ["boss", "get", "b001"],
        ),
        "encounter": (
            encounter_setup,
            lambda cursor: encounter_mcp.encounter_get("c001/e001", cursor=cursor),
            lambda: encounter_mcp.encounter_update("c001/e001", CONTINUED_BODY + "edit"),
            ["encounter", "get", "c001/e001"],
        ),
    }


@pytest.mark.parametrize("domain", ["world", "lore", "region", "campaign", "boss", "encounter"])
def test_get_continuation_reassembles_and_matches_cli(
    domain: str, seed_world: Callable[[], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    from cac.core import budget, config, references

    setup, get, edit, args = _continuation_domains()[domain]
    seed_world()
    setup()
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 2000)
    pages, cursor, cursors = [], None, []
    while True:
        page = get(cursor)
        assert len(references.encoded(page)) <= 2000
        assert ".sourcebook" not in page.get("notice", "")
        cli = runner.invoke(app, args + (["--cursor", cursor] if cursor else []))
        assert cli.exit_code == 0, cli.output
        assert page["body"] in cli.output and ".sourcebook" not in cli.output
        pages.append(page["body"])
        cursor = page.get("next_cursor")
        if cursor is None:
            assert "next_cursor:" not in cli.output
            break
        assert f"next_cursor: {cursor}" in cli.output and "[TRUNCATED" in cli.output
        cursors.append(cursor)
    assert len(pages) > 2 and "".join(pages) == CONTINUED_BODY
    edit()
    with pytest.raises(budget.InvalidCursorError):
        get(cursors[0])
    stale = runner.invoke(app, args + ["--cursor", cursors[0]])
    assert stale.exit_code == 1 and "stale" in stale.output
    invalid = runner.invoke(app, args + ["--cursor", "not-a-cursor"])
    assert invalid.exit_code == 1


def test_archived_records_continue_by_short_reference(
    seed_world: Callable[[], None], monkeypatch: pytest.MonkeyPatch
) -> None:
    from cac.core import config
    from cac.mcp import campaign as campaign_mcp
    from cac.mcp import encounter as encounter_mcp

    seed_world()
    campaign_mcp.campaign_create("c001-old", CONTINUED_BODY)
    encounter_mcp.encounter_create("e001-old", CONTINUED_BODY, campaign="c001")
    encounter_mcp.encounter_abandon("c001/e001", "Dropped")
    campaign_mcp.campaign_abandon("c001", "Dropped")
    campaign_mcp.campaign_archive("c001")
    monkeypatch.setattr(config, "RESPONSE_BUDGET", 2000)
    for get in (
        lambda cursor: campaign_mcp.campaign_get("c001", cursor=cursor),
        lambda cursor: encounter_mcp.encounter_get("c001/e001", cursor=cursor),
    ):
        pages, cursor = [], None
        while True:
            page = get(cursor)
            pages.append(page["body"])
            cursor = page.get("next_cursor")
            if cursor is None:
                break
        assert page["metadata"]["archived"] is True
        # Abandonment appended a log entry after the original body.
        assert "".join(pages).startswith(CONTINUED_BODY)
