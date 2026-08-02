from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from cac.core import templates

_TEMPLATE_PACKAGE = "docs"
_DOC_RESOURCE_PACKAGE = "cac.core.templates.docs"


class DocNotFoundError(ValueError):
    """Raised when a named doc is not registered."""


@dataclass(frozen=True)
class DocEntry:
    name: str
    filename: str
    summary: str


_DOCS: dict[str, DocEntry] = {
    "workflow": DocEntry(
        name="workflow",
        filename="workflow.md",
        summary=(
            "The Workflow Reference Guide: the .sourcebook domain model's structure, status "
            "lifecycles, cross-type connections, and the encounter review/approval procedure. "
            "Read this when a task needs the exact rule, not just a summary of it."
        ),
    ),
}


def list_docs() -> list[tuple[str, str]]:
    """Return (name, summary) pairs for every registered doc, sorted by name."""
    return [(entry.name, entry.summary) for entry in sorted(_DOCS.values(), key=lambda entry: entry.name)]


def doc_summary(name: str) -> str:
    return _entry(name).summary


def read_doc(name: str) -> str:
    """Return a registered doc's full body."""
    entry = _entry(name)
    return templates.load(_TEMPLATE_PACKAGE, entry.filename)


def doc_source_path(name: str) -> Path:
    """Return the packaged doc's real filesystem path, for a truncation fallback notice."""
    entry = _entry(name)
    return Path(str(resources.files(_DOC_RESOURCE_PACKAGE) / entry.filename))


def _entry(name: str) -> DocEntry:
    try:
        return _DOCS[name]
    except KeyError:
        raise DocNotFoundError(f"Doc {name!r} does not exist.") from None
