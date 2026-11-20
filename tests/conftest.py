import importlib.util
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

# The corpus and the perf and golden tests' fixture suites are analysed, never run.
collect_ignore = ["corpus", "perf/suite", "golden/suite"]

# Ends a generated test file so its tests carry a category marker (no DS901) while
# every line above it, and so every finding's line, stays where it was.
UNIT_MARK = "\nimport pytest\n\npytestmark = pytest.mark.unit\n"


@pytest.fixture
def unit_mark():
    """The lines that end a generated test file so its tests carry a category marker
    (no DS901), leaving every line above them in place."""
    return UNIT_MARK


# The stock finding, DS101, is off by default until it is proven (#171), so a run that
# reports it turns it on in its config.
def ini_text(lines, on):
    """A `[pytest]` section turning DS101 and each `CODE=level` in `on` on, then each
    line given."""
    levels = "".join(f"\n    {entry}" for entry in ("DS101=fail", *on))
    body = "".join(f"{line}\n" for line in lines)
    return f"[pytest]\ndrill_sergeant_levels ={levels}\n{body}"


@pytest.fixture
def cli_ini(tmp_path):
    """Write `pytest.ini` in `tmp_path`: DS101 and each `CODE=level` in `on` on, then
    each line given, and return its path."""

    def write(*lines: str, on: tuple[str, ...] = ()):
        path = tmp_path / "pytest.ini"
        path.write_text(ini_text(lines, on))
        return path

    return write


@pytest.fixture
def drill_ini(pytester):
    """Write the ini file of `pytester`'s run: DS101 and each `CODE=level` in `on` on,
    then each line given, and return its path."""

    def write(*lines: str, on: tuple[str, ...] = ()):
        return pytester.makeini(ini_text(lines, on))

    return write


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
def clean_test(tmp_path):
    """A test file in `tmp_path`, `test_ok.py`, holding one test with no finding."""
    path = tmp_path / "test_ok.py"
    path.write_text("def test_ok():\n    assert sum([1, 1]) == 2\n" + UNIT_MARK)
    return path


@pytest.fixture
def unseeded_random_test(tmp_path):
    """A test file in `tmp_path` holding one test whose only finding is from a check
    on by default: an unseeded random draw (DS803 on line 4)."""
    path = tmp_path / "test_draw.py"
    path.write_text(
        "import random\n\ndef test_draw():\n    assert random.random() < 2\n"
        + UNIT_MARK
    )
    return path


@pytest.fixture
def assertion_free_test(tmp_path, cli_ini):
    """A test file in `tmp_path` holding one test with no real assertion (DS101 on
    line 1), and a `pytest.ini` beside it that turns DS101 on."""
    cli_ini()
    path = tmp_path / "test_it.py"
    path.write_text("def test_it():\n    run()\n" + UNIT_MARK)
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
def lazy_file(pytester, drill_ini):
    """Write a test file at a path in `pytester`'s temp dir holding one passing test
    with no real assertion per name given (one DS101 each, the first on line 1), and
    an ini file that turns DS101 on. Each test prints its own name, so no two are
    near-duplicates (DS502)."""
    drill_ini()

    def write(path: str, *names: str):
        file = pytester.path / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            "".join(f"def {name}():\n    print({name}.__name__)\n" for name in names)
            + UNIT_MARK
        )
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
        + UNIT_MARK
    )


@pytest.fixture
def long_named_test(tmp_path, cli_ini):
    """A test file in `tmp_path` holding one test with no real assertion (DS101 on
    line 1) whose name makes its location line longer than a narrow terminal, and a
    `pytest.ini` beside it that turns DS101 on."""
    cli_ini()
    path = tmp_path / "test_long.py"
    path.write_text(f"def test_{'very_' * 10}long():\n    run()\n" + UNIT_MARK)
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
def special_casing_module():
    """Write `app.py`, production code that checks whether pytest is running (DS403
    on line 4), into a directory, and return its path."""

    def write(directory):
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "app.py"
        path.write_text("import os\nimport sys\n\nTESTING = 'pytest' in sys.modules\n")
        return path

    return write


@pytest.fixture
def pasted_across_files():
    """The corpus's three files, in path order, that each paste the same setup
    block into one test (one DS501, on the first file's block)."""
    folder = Path(__file__).parent / "corpus" / "copy-paste-setup" / "cross-file"
    return sorted(folder.glob("*.py"))


@pytest.fixture
def write_test_file(tmp_path):
    """Write source to a file in `tmp_path`, `test_it.py` unless named, ended by
    `UNIT_MARK`, and return its path."""

    def write(source: str, name: str = "test_it.py"):
        path = tmp_path / name
        path.write_text(source + UNIT_MARK)
        return path

    return write


@pytest.fixture
def helper_caller(write_test_file, tmp_path):
    """A test file in `tmp_path` whose one test only calls `check_total`, imported
    from `checks.py` beside it, which isn't written yet; returns the test file and
    where the helper module goes."""
    path = write_test_file(
        "from .checks import check_total\n\ndef test_total():\n    check_total([1, 2])\n"
    )
    return path, tmp_path / "checks.py"


@pytest.fixture
def waived_test(tmp_path, cli_ini):
    """A test file in `tmp_path`, `test_waived.py`, holding one test whose only
    finding (DS101 on line 1) is waived with the reason `smoke test`, and a
    `pytest.ini` beside it that turns DS101 on."""
    cli_ini()
    path = tmp_path / "test_waived.py"
    path.write_text(
        "def test_waived():  # drill: waive DS101 -- smoke test\n    run()\n"
        + UNIT_MARK
    )
    return path


@pytest.fixture
def unmarked_test_at(tmp_path):
    """Write a file at a path under `tmp_path` holding one test whose only finding
    is its missing category marker (DS901 on line 1), and return its path."""

    def write(relative: str):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def test_total():\n    assert total([1, 2]) == 3\n")
        return path

    return write


@pytest.fixture
def watch():
    """Start watching a directory: return a function that lists the files under it
    written since (made, replaced or changed), by inode and modification time."""

    def files(directory: Path) -> dict[Path, tuple[int, int]]:
        return {
            p: (p.stat().st_ino, p.stat().st_mtime_ns)
            for p in directory.rglob("*")
            if p.is_file()
        }

    def start(directory: Path):
        before = files(directory)

        def written() -> list[Path]:
            return sorted(p for p, s in files(directory).items() if before.get(p) != s)

        return written

    return start


@pytest.fixture
def golden_suite():
    """The golden suite's test files, in path order: small and fixed, with
    findings in them."""
    return sorted((Path(__file__).parent / "golden" / "suite").glob("*.py"))


@pytest.fixture
def cache_dir(tmp_path):
    """A cache directory in `tmp_path`, `cache/`, not yet made."""
    return tmp_path / "cache"


@pytest.fixture
def try_checks(tmp_path, monkeypatch, capsys):
    """Run `scripts/try_checks.py <args>`, what `just try` runs, from `tmp_path`, and
    return its exit code and everything it printed."""
    script = Path(__file__).parent.parent / "scripts" / "try_checks.py"
    spec = importlib.util.spec_from_file_location("try_checks", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.chdir(tmp_path)

    def run(*args: str):
        code = module.main(list(args))
        printed = capsys.readouterr()
        return code, printed.out + printed.err

    return run
