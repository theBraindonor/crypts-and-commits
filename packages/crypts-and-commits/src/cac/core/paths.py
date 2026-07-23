from pathlib import Path

from cac.core.config import SOURCEBOOK_DIR_NAME


def sourcebook_dir(root: Path) -> Path:
    return root / SOURCEBOOK_DIR_NAME
