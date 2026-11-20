import os
from pathlib import Path

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


@pytest.fixture
def assertion_free_test(tmp_path):
    """A test file in `tmp_path` holding one test with no real assertion (DS101 on
    line 1)."""
    path = tmp_path / "test_it.py"
    path.write_text("def test_it():\n    run()\n")
    return path


@pytest.fixture
def drill(pytester, monkeypatch):
    """Run pytest in `pytester`'s temp dir with the plugin installed, as a user would,
    in a fixed order, and return pytester's result.

    The run's xdist workers measure no coverage: pytest-cov would have them write
    into this suite's coverage data, which they can't be combined with."""
    for name in [n for n in os.environ if n.startswith("COV_CORE_")]:
        monkeypatch.delenv(name)

    def run(*args: str):
        return pytester.runpytest("-p", "no:randomly", *args)

    return run


@pytest.fixture
def lazy_file(pytester):
    """Write a test file at a path in `pytester`'s temp dir holding one passing test
    with no real assertion per name given (one DS101 each, the first on line 1)."""

    def write(path: str, *names: str):
        file = pytester.path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("".join(f"def {name}():\n    print('hi')\n" for name in names))
        return file

    return write


@pytest.fixture
def lazy_test(lazy_file):
    """A test file in `pytester`'s temp dir, `test_lazy.py`, holding one passing test
    with no real assertion (DS101 on line 1)."""
    return lazy_file("test_lazy.py", "test_lazy")


@pytest.fixture
def failing_test(pytester):
    """A test file in `pytester`'s temp dir, `test_broken.py`, holding one failing
    test."""
    return pytester.makepyfile(
        test_broken="def test_broken():\n    assert sorted([2, 1]) == [2, 1]\n"
    )


@pytest.fixture
def long_named_test(tmp_path):
    """A test file in `tmp_path` holding one test with no real assertion (DS101 on
    line 1) whose name makes its location line longer than a narrow terminal."""
    path = tmp_path / "test_long.py"
    path.write_text(f"def test_{'very_' * 10}long():\n    run()\n")
    return path


@pytest.fixture
def wrapped():
    """Split a report at a fact (`Found:`, `Why:`, `Fix:`): return the lines indented
    exactly under the fact's text after its first line, and the line after them."""

    def split(output: str, label: str) -> tuple[list[str], str]:
        lines = output.splitlines()
        start = next(i for i, ln in enumerate(lines) if ln.lstrip().startswith(label))
        first = lines[start]
        column = len(first) - len(first[first.index(label) + len(label) :].lstrip())
        end = start + 1
        while end < len(lines) and len(lines[end]) - len(lines[end].lstrip()) == column:
            end += 1
        return lines[start + 1 : end], lines[end] if end < len(lines) else ""

    return split


@pytest.fixture
def pasted_across_files():
    """The corpus's three files, in path order, that each paste the same setup
    block into one test (one DS501, on the first file's block)."""
    folder = Path(__file__).parent / "corpus" / "copy-paste-setup" / "cross-file"
    return sorted(folder.glob("*.py"))
