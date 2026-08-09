import os
from collections.abc import Callable
from pathlib import Path

# rich.Console() bakes width/height/color-system into _width/_height/_color_system
# at construction time (see rich.console.Console.__init__), not per-print - and
# _color_system is derived from is_terminal, which at construction time reflects
# the real terminal actually running pytest (CliRunner only redirects sys.stdout
# later, per-invoke). cac's CLI modules each build a module-level
# `console = Console()` at import time, so this must run before `cac.cli.app`
# (and everything it imports) is first imported below - a per-test monkeypatch
# fixture would always be too late, since collection already imported every cli
# module before any fixture runs. TTY_COMPATIBLE=0 is checked first in
# Console.is_terminal (ahead of isatty()), forcing color detection off
# regardless of the real terminal; NO_COLOR is kept too since some rendering
# paths (e.g. export_text) consult it directly. COLUMNS/LINES pin word-wrap
# width the same way. Together these make `result.output` assertions
# deterministic regardless of the real terminal window pytest happens to run in.
os.environ["TTY_COMPATIBLE"] = "0"
os.environ["COLUMNS"] = "200"
os.environ["LINES"] = "50"
os.environ["NO_COLOR"] = "1"
os.environ.pop("FORCE_COLOR", None)

import pytest
from cac.cli.app import app
from cac.core import bootstrap, world
from typer.testing import CliRunner


@pytest.fixture
def create_campaign() -> Callable[..., None]:
    runner = CliRunner()

    def _create(name: str = "opening-gambit", body: str = "Body.") -> None:
        runner.invoke(app, ["campaign", "create", name, "--body", body])

    return _create


@pytest.fixture
def open_campaign() -> Callable[..., None]:
    runner = CliRunner()

    def _open(name: str = "opening-gambit") -> None:
        runner.invoke(app, ["campaign", "open", name])

    return _open


@pytest.fixture
def seed_world() -> Callable[[], None]:
    def _seed() -> None:
        root = Path.cwd()
        bootstrap.initialize(root)
        world.initialize_world(root)

    return _seed
