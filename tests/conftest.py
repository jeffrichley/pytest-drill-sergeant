import os

import pytest
from typer.testing import CliRunner

from pytest_drill_sergeant.cli import app

# Output reads the same on a laptop and in CI. Typer forces colour when any of these is
# set (GITHUB_ACTIONS is, on CI) and reads them once, at import, so they go before any
# test module imports the CLI.
for name in ("GITHUB_ACTIONS", "FORCE_COLOR", "PY_COLORS"):
    os.environ.pop(name, None)
os.environ["NO_COLOR"] = "1"
os.environ["COLUMNS"] = "100"

pytest_plugins = ["pytester"]

# The corpus is analysed by the engine, never run.
collect_ignore = ["corpus"]


@pytest.fixture
def cli(tmp_path, monkeypatch):
    """Run `drill-sergeant <args>` as a user would, from a temp dir, and return typer's
    result."""
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    def run(*args: str):
        return runner.invoke(app, list(args), prog_name="drill-sergeant")

    return run
