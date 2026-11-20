"""Rewrite golden/check.txt as the golden test in test_cli.py runs the CLI.

Run it with `just golden`, then review `git diff tests/golden`. The environment is
pinned as conftest.py pins it, before the CLI is imported, and the suite is checked
from a temp copy, as the test checks it.
"""

import os
import shutil
import tempfile
from pathlib import Path

for name in ("GITHUB_ACTIONS", "FORCE_COLOR", "PY_COLORS"):
    os.environ.pop(name, None)
os.environ["NO_COLOR"] = "1"
os.environ["COLUMNS"] = "100"

from typer.testing import CliRunner  # noqa: E402

from pytest_drill_sergeant.cli import app  # noqa: E402

GOLDEN = Path(__file__).resolve().parent

with tempfile.TemporaryDirectory() as tmp:
    shutil.copytree(GOLDEN / "suite", Path(tmp) / "suite")
    os.chdir(tmp)
    result = CliRunner().invoke(
        app, ["check", "--show-waived", "suite"], prog_name="drill-sergeant"
    )
    os.chdir(GOLDEN)

(GOLDEN / "check.txt").write_text(result.output, newline="\n")
print(f"wrote {GOLDEN / 'check.txt'} (exit {result.exit_code})")
