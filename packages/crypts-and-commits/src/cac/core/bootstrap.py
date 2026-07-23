from pathlib import Path

from cac.core.paths import sourcebook_dir


def initialize(root: Path) -> tuple[Path, bool]:
    """Create the .sourcebook directory under root.

    Returns the sourcebook directory path and whether it was newly created.
    """
    directory = sourcebook_dir(root)
    created = not directory.exists()
    directory.mkdir(exist_ok=True)
    return directory, created
