"""Boss planning records. Campaign coupling and candidate evaluation are separate work."""

from pathlib import Path
from typing import Any

import frontmatter

from cac.core import boss_provenance, frontmatter_utils, templates, world
from cac.core.config import ARCHIVE_DIR_NAME, BOSS_DIR_NAME, BOSS_STATUSES, NAME_PATTERN, RESERVED_NAMES
from cac.core.paths import sourcebook_dir


class BossError(ValueError):
    """Invalid boss state, name, storage, or dependency graph."""


class BossNotFoundError(FileNotFoundError):
    """A canonical boss name has no retained record."""


class BossAlreadyExistsError(FileExistsError):
    """A name is already retained in live storage or the archive."""


def validate_name(name: str) -> None:
    if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES:
        raise BossError(f"Invalid boss name {name!r}: use letters, numbers, underscores, hyphens, or periods.")


def boss_dir(root: Path, *, archived: bool = False) -> Path:
    base = sourcebook_dir(root)
    return base / ARCHIVE_DIR_NAME / BOSS_DIR_NAME if archived else base / BOSS_DIR_NAME


def _safe_path(root: Path, path: Path) -> Path:
    # Reject links/junctions and non-directory ancestors, including dangling links.
    base = sourcebook_dir(root)
    for part in (path, *path.parents):
        if part == base.parent:
            break
        if part.is_symlink() or getattr(part, "is_junction", lambda: False)():
            raise BossError(f"Boss storage collision at {part}: links are not record locations.")
        if part != path and part.exists() and not part.is_dir():
            raise BossError(f"Boss storage collision at {part}: expected a directory.")
    if path.exists() and not path.is_file():
        raise BossError(f"Boss storage collision at {path}: expected a markdown record.")
    if path.resolve() != base.resolve() / path.relative_to(base):
        raise BossError(f"Boss storage path escapes its record directory: {path}.")
    return path


def _locations(root: Path, name: str) -> tuple[Path, Path]:
    validate_name(name)
    return tuple(_safe_path(root, boss_dir(root, archived=a) / f"{name}.md") for a in (False, True))


def boss_path(root: Path, name: str) -> Path:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() and archived.exists():
        raise BossError(f"Boss {name!r} is ambiguous: both live and archived records exist.")
    if live.exists():
        return live
    if archived.exists():
        return archived
    raise BossNotFoundError(f"Boss {name!r} does not exist.")


def _names(root: Path, archived: bool) -> list[str]:
    directory = boss_dir(root, archived=archived)
    # Validate the directory even if no records match.
    _safe_path(root, directory / "_probe.md")
    if not directory.exists():
        return []
    names = []
    for path in sorted(directory.iterdir()):
        if path.suffix == ".md":
            validate_name(path.stem)
            _safe_path(root, path)
            names.append(path.stem)
    return names


def list_bosses(root: Path, *, include_archived: bool = False) -> list[str]:
    world.read_world(root)
    live, archived = _names(root, False), _names(root, True)
    overlap = sorted(set(live) & set(archived))
    if overlap:
        raise BossError(f"Ambiguous live/archive boss names: {', '.join(overlap)}.")
    return sorted(live + archived) if include_archived else live


def _load(root: Path, name: str) -> tuple[Path, frontmatter.Post]:
    path = boss_path(root, name)
    post = frontmatter.load(path)
    if post.get("name") != name or post.get("status") not in BOSS_STATUSES:
        raise BossError(f"Boss {name!r} has inconsistent name or invalid status metadata.")
    archived = path.parent == boss_dir(root, archived=True)
    if type(post.get("archived", False)) is not bool or post.get("archived", False) != archived:
        raise BossError(f"Boss {name!r} has an archive flag/location mismatch.")
    campaign = post.get("campaign")
    if campaign is not None and (not isinstance(campaign, str) or not campaign):
        raise BossError(f"Boss {name!r} has malformed campaign metadata.")
    if "provenance" in post.metadata:
        snapshot = boss_provenance.validate(post["provenance"])
        if snapshot["progress"] == "completed" and (post["status"] != "vanquished" or campaign is not None):
            raise BossError(f"Boss {name!r} has inconsistent external completion state.")
    return path, post


def read_metadata(root: Path, name: str) -> tuple[dict[str, Any], str]:
    _, post = _load(root, name)
    return dict(post.metadata), post.content


def template_body() -> str:
    return frontmatter.loads(templates.load("sourcebook", "boss.md")).content


def _prepare_boss(root: Path, name: str, body: str, summary: str) -> tuple[Path, frontmatter.Post]:
    world.read_world(root)
    live, archived = _locations(root, name)
    if live.exists() or archived.exists():
        raise BossAlreadyExistsError(f"Boss {name!r} already exists, live or archived.")
    # Inventory validates the reserved namespace and directory collisions before any write.
    list_bosses(root, include_archived=True)
    post = frontmatter.loads(templates.load("sourcebook", "boss.md"))
    post["name"] = name
    post.content = body
    frontmatter_utils.set_summary_attribute(post, summary)
    frontmatter_utils.stamp_created(post, root)
    return live, post


def create_boss(root: Path, name: str, body: str, summary: str) -> Path:
    live, post = _prepare_boss(root, name, body, summary)
    live.parent.mkdir(parents=True, exist_ok=True)
    frontmatter_utils.write_post(root, live, post)
    return live


def record_boss(
    root: Path,
    name: str,
    body: str,
    summary: str,
    progress: str,
    source: str,
    message: str,
    completed_on: str | None = None,
    depends_on: list[str] | None = None,
) -> Path:
    """Capture one existing roadmap goal without inventing CAC execution history."""
    from cac.core import references
    from cac.core.recovery import Recovery

    if not isinstance(body, str) or not isinstance(summary, str):
        raise BossError("Boss body and summary must be text.")
    provenance = boss_provenance.validate(
        {"kind": "roadmap", "progress": progress, "source": source, "message": message, "completed_on": completed_on}
    )
    live, post = _prepare_boss(root, name, body, summary)
    if depends_on is None:
        depends_on = []
    if not isinstance(depends_on, list):
        raise BossError("depends_on must be a list of boss references.")
    inventory = references.Inventory(root)
    targets = []
    for target in depends_on:
        if target == name:
            raise BossError("A recorded boss cannot depend on itself.")
        targets.append(inventory.resolve("boss", target))
    if len(set(targets)) != len(targets):
        raise BossError("Duplicate prerequisite identities after reference resolution.")
    graph, records = {}, {}
    for canonical in list_bosses(root, include_archived=True):
        _, record = _load(root, canonical)
        records[canonical] = record
        graph[canonical] = _dependencies(record, canonical)
    _validate_graph(graph)
    for target in targets:
        if records[target]["status"] == "withdrawn":
            raise BossError(f"Cannot add withdrawn prerequisite {target!r}.")
    graph[name] = sorted(targets)
    _validate_graph(graph)
    post["provenance"] = provenance
    post["depends_on"] = graph[name]
    post["status"] = "vanquished" if progress == "completed" else "proposed"
    _minimum_output(root, name, post)
    with Recovery(root, [live]):
        live.parent.mkdir(parents=True, exist_ok=True)
        frontmatter_utils.write_post(root, live, post)
    return live


def _minimum_output(root: Path, name: str, post: frontmatter.Post) -> None:
    from cac.core import config, references

    metadata = dict(post.metadata)
    summary = metadata.pop("summary", "")
    minimum = {
        "metadata": metadata,
        "summary": summary,
        "body": "",
        "identity": {"canonical": name, "short": None, "reason": "ambiguous"},
    }
    # Reserve the continuation notice/cursor and the longest possible identity, with a
    # name-length margin, so a later get can always return at least one body page.
    path = boss_dir(root, archived=True) / f"{name}.md"
    if len(references.encoded(minimum)) + 400 + 2 * len(str(path)) > config.RESPONSE_BUDGET:
        raise BossError("Boss metadata/provenance and continuation notice exceed the response budget before writes.")


def _editable(post: frontmatter.Post, name: str, statuses: tuple[str, ...] = ("proposed", "available")) -> None:
    if post.get("archived", False) or post.get("campaign") is not None or post["status"] not in statuses:
        raise BossError(f"Boss {name!r} is frozen: requires unarchived, unassigned status in {statuses}.")


def _save(root: Path, path: Path, post: frontmatter.Post) -> Path:
    frontmatter_utils.stamp_updated(post, root)
    frontmatter_utils.write_post(root, path, post)
    return path


def update_boss(root: Path, name: str, body: str, summary: str) -> Path:
    path, post = _load(root, name)
    _editable(post, name)
    post.content = body
    frontmatter_utils.set_summary_attribute(post, summary)
    return _save(root, path, post)


def _transition(root: Path, name: str, allowed: tuple[str, ...], status: str) -> Path:
    path, post = _load(root, name)
    _editable(post, name, allowed)
    post["status"] = status
    return _save(root, path, post)


def make_available(root: Path, name: str) -> Path:
    return _transition(root, name, ("proposed",), "available")


def withdraw(root: Path, name: str) -> Path:
    return _transition(root, name, ("proposed", "available"), "withdrawn")


def reactivate(root: Path, name: str) -> Path:
    return _transition(root, name, ("withdrawn",), "proposed")


def archive_boss(root: Path, name: str) -> Path:
    from cac.core import coupling
    from cac.core.recovery import Recovery

    path, post = _load(root, name)
    external = boss_provenance.external_completion(post.metadata)
    allowed = ("vanquished",) if external else ("withdrawn",)
    _editable(post, name, allowed)
    destination = _locations(root, name)[1]
    if destination.exists():
        raise BossAlreadyExistsError(f"Archive destination already exists for boss {name!r}.")
    post["archived"] = True
    frontmatter_utils.stamp_updated(post, root)
    if "provenance" in post.metadata:
        _minimum_output(root, name, post)
    original = path.read_bytes()
    coupling._body_suffix(original)
    with Recovery(root, [path, destination]):
        if external:
            coupling._write_boss(root, destination, post, original)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            frontmatter_utils.write_post(root, destination, post)
        path.unlink()
    return destination


def _dependencies(post: frontmatter.Post, name: str) -> list[str]:
    values = post.get("depends_on", [])
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise BossError(f"Boss {name!r} has malformed depends_on: expected a list of canonical names.")
    for value in values:
        validate_name(value)
    if len(values) != len(set(values)):
        raise BossError(f"Boss {name!r} has duplicate stored dependency edges.")
    return values.copy()


def _validate_graph(graph: dict[str, list[str]]) -> None:
    for name, dependencies in graph.items():
        for target in dependencies:
            if target not in graph:
                raise BossError(
                    f"Boss {name!r} references missing prerequisite {target!r}; remove or repair that edge."
                )
    # Iterative DFS supports long prerequisite chains without Python recursion limits.
    done: set[str] = set()
    for start in graph:
        active: dict[str, None] = {}
        stack = [(start, False)]
        while stack:
            name, leaving = stack.pop()
            if leaving:
                active.pop(name, None)
                done.add(name)
            elif name in active:
                raise BossError(f"Boss dependency cycle: {' -> '.join((*active, name))}.")
            elif name not in done:
                active[name] = None
                stack.append((name, True))
                stack.extend((target, False) for target in reversed(graph[name]))


def _change_dependency(root: Path, name: str, dependency: str, *, remove: bool) -> Path:
    path, post = _load(root, name)
    _editable(post, name)
    validate_name(dependency)
    graph = {}
    records = {}
    for canonical in list_bosses(root, include_archived=True):
        _, record = _load(root, canonical)
        records[canonical] = record
        graph[canonical] = _dependencies(record, canonical)
    edges = graph[name]
    if remove:
        if dependency not in edges:
            raise BossError(f"Boss {name!r} has no dependency on {dependency!r}.")
        edges.remove(dependency)
    else:
        if dependency == name or dependency in edges:
            raise BossError(f"Self or duplicate dependency {name!r} -> {dependency!r}.")
        if dependency not in records:
            raise BossNotFoundError(f"Prerequisite boss {dependency!r} does not exist.")
        if records[dependency]["status"] == "withdrawn":
            raise BossError(f"Cannot add withdrawn prerequisite {dependency!r}.")
        # Adding must not conceal pre-existing graph damage.
        _validate_graph(graph)
        edges.append(dependency)
    _validate_graph(graph)
    post["depends_on"] = sorted(edges)
    return _save(root, path, post)


def assign_dependency(root: Path, name: str, dependency: str) -> Path:
    return _change_dependency(root, name, dependency, remove=False)


def unassign_dependency(root: Path, name: str, dependency: str) -> Path:
    return _change_dependency(root, name, dependency, remove=True)


def assign_campaign(root: Path, name: str, campaign_name: str, body: str) -> dict[str, Any]:
    """Promote an eligible boss into a new, deliberately supplied draft campaign."""
    from cac.core import coupling

    return coupling.assign_campaign(root, name, campaign_name, body)


def get_payload(root: Path, name: str) -> dict[str, Any]:
    """The unbudgeted boss_get result shared by CLI and MCP, before identity and budget fitting."""
    metadata, body = read_metadata(root, name)
    summary = metadata.pop("summary", "")
    return {"metadata": metadata, "summary": summary, "body": body}
