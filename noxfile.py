"""Pre-release check: run crypts-and-commits' test suite under every supported Python version.

Not part of the routine dev loop - invoke explicitly via `pdm run nox`.
Uses the "uv" venv backend so missing interpreters (e.g. a Python version not
yet installed on this machine) are downloaded automatically.
"""

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.11", "3.12", "3.13", "3.14"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    session.install("./packages/crypts-and-commits", "pytest")
    session.run("pytest", "packages/crypts-and-commits/tests", "-q")
