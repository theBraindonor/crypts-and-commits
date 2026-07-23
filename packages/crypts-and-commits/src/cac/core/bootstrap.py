from pathlib import Path

SOURCEBOOK_DIR_NAME = ".sourcebook"


def initialize(root: Path) -> tuple[Path, bool]:
    """Create the .sourcebook directory under root.

    Returns the sourcebook directory path and whether it was newly created.
    """
    sourcebook_dir = root / SOURCEBOOK_DIR_NAME
    created = not sourcebook_dir.exists()
    sourcebook_dir.mkdir(exist_ok=True)
    return sourcebook_dir, created
