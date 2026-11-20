"""The duplication family (DS5xx): tests that repeat what one place should hold.

Its checks compare per-file summaries across every file in the run, never the files
themselves (cross-file analysis), so a block pasted into tests in different files
is caught as surely as one pasted within a file.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.checks.base import (
    Check,
    Hit,
    Statement,
    Summaries,
    Thresholds,
)
from pytest_drill_sergeant.findings import Level


@dataclass(frozen=True)
class _Setup:
    """One test's setup, with where the test is."""

    path: Path
    test: str
    statements: tuple[Statement, ...]


@dataclass(frozen=True)
class _Copy:
    """Where a pasted block starts in one test's setup."""

    setup: _Setup
    start: int

    def statement(self, offset: int) -> Statement | None:
        """The statement `offset` past the block's start, if the setup has one."""
        index = self.start + offset
        statements = self.setup.statements
        return statements[index] if index < len(statements) else None


def _setups(summaries: Summaries) -> list[_Setup]:
    return [
        _Setup(path=path, test=test.name, statements=test.setup)
        for path, summary in summaries
        for test in summary.tests
    ]


def _windows(setups: list[_Setup], size: int) -> dict[tuple[str, ...], list[_Copy]]:
    """Every run of `size` setup statements, by fingerprints, in first-seen order.

    A run a test repeats within its own setup is counted once for that test.
    """
    windows: dict[tuple[str, ...], list[_Copy]] = {}
    for setup in setups:
        prints = [s.fingerprint for s in setup.statements]
        for start in range(len(prints) - size + 1):
            copies = windows.setdefault(tuple(prints[start : start + size]), [])
            if not copies or copies[-1].setup is not setup:
                copies.append(_Copy(setup, start))
    return windows


def _length(copies: list[_Copy], size: int) -> int:
    """How far every copy runs on alike, from a shared run of `size` statements."""
    length = size
    while True:
        nexts = [copy.statement(length) for copy in copies]
        if (
            any(s is None for s in nexts)
            or len({s.fingerprint for s in nexts if s}) > 1
        ):
            return length
        length += 1


def _where(copy: _Copy, anchor: Path) -> str:
    line = copy.setup.statements[copy.start].line
    if copy.setup.path == anchor:
        return f"`{copy.setup.test}` (line {line})"
    return f"`{copy.setup.test}` ({copy.setup.path.as_posix()}, line {line})"


def _fixture_name(block: list[Statement]) -> str:
    """The fixture to suggest: named for the last name the block binds."""
    names = [name for statement in block for name in statement.binds]
    return f"a fixture, e.g. `{names[-1]}`," if names else "a fixture"


def _find_copy_paste_setup(
    summaries: Summaries, thresholds: Thresholds
) -> Iterator[tuple[Path, Hit]]:
    # A block is at least one statement, and is pasted only if two tests hold it.
    size = max(thresholds.duplicate_setup_min_statements, 1)
    least = max(thresholds.duplicate_setup_min_tests, 2)
    reported: set[tuple[int, int]] = set()  # (setup id, statement index)
    for copies in _windows(_setups(summaries), size).values():
        if len(copies) < least:
            continue
        length = _length(copies, size)
        spans = [{(id(c.setup), c.start + i) for i in range(length)} for c in copies]
        if all(span & reported for span in spans):
            continue
        reported.update(*spans)
        first, others = copies[0], copies[1:]
        block = list(first.setup.statements[first.start : first.start + length])
        lines = f"lines {block[0].line}-{block[-1].end_line}"
        tests = ", ".join(_where(copy, first.setup.path) for copy in others)
        yield (
            first.setup.path,
            Hit.at(
                first.setup.test,
                block[0].line,
                found=(
                    f"shares {length} setup statements ({lines}) with "
                    f"{len(others)} other tests: {tests}."
                ),
                fix=(
                    f"move {lines} into {_fixture_name(block)} and request it "
                    f"here and in {tests}."
                ),
            ),
        )


COPY_PASTE_SETUP = Check(
    code="DS501",
    name="copy-paste-setup",
    default_level=Level.FAIL,
    voice=(
        "LISTEN UP, RECRUIT! You wrote the same setup over and over like a broken "
        "record!",
        "Copy, paste, copy, paste! That's not engineering, that's a PHOTOCOPIER, "
        "maggot!",
        "One fixture, recruit! Not the same orders barked in every tent!",
    ),
    why=(
        "Pasted setup drifts apart copy by copy, every change to it has to be made "
        "in each test, and it buries what makes each test different."
    ),
    explain=(
        "Flags a block of setup statements pasted into several tests, in one file or "
        "across files: at least `drill_sergeant_duplicate_setup_min_statements` "
        "statements in a row (3 by default), alike in every name and literal, in at "
        "least `drill_sergeant_duplicate_setup_min_tests` tests (3 by default). A "
        "test's setup is its statements before the first one that holds a real "
        "assertion. One finding per block, on its first occurrence, names the other "
        "tests that hold it. Setup that differs in a value is not a copy: if the "
        "tests differ only in their values, parametrize them instead. Move the block "
        "into a fixture and have each test request it."
    ),
    bad_example=(
        "def test_order_total(tmp_path):\n"
        "    catalog = Catalog(tmp_path)\n"
        "    catalog.add('apple', price=3)\n"
        "    order = Order(catalog)\n"
        "    order.add('apple', quantity=2)\n"
        "    assert order.total() == 6\n"
        "\n"
        "\n"
        "def test_order_pay(tmp_path):\n"
        "    catalog = Catalog(tmp_path)\n"
        "    catalog.add('apple', price=3)\n"
        "    order = Order(catalog)\n"
        "    order.pay()\n"
        "    assert order.status == 'paid'\n"
        "\n"
        "\n"
        "def test_order_cancel(tmp_path):\n"
        "    catalog = Catalog(tmp_path)\n"
        "    catalog.add('apple', price=3)\n"
        "    order = Order(catalog)\n"
        "    order.cancel()\n"
        "    assert order.status == 'cancelled'\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.fixture\n"
        "def order(tmp_path):\n"
        "    catalog = Catalog(tmp_path)\n"
        "    catalog.add('apple', price=3)\n"
        "    return Order(catalog)\n"
        "\n"
        "\n"
        "def test_order_total(order):\n"
        "    order.add('apple', quantity=2)\n"
        "    assert order.total() == 6\n"
        "\n"
        "\n"
        "def test_order_pay(order):\n"
        "    order.pay()\n"
        "    assert order.status == 'paid'\n"
        "\n"
        "\n"
        "def test_order_cancel(order):\n"
        "    order.cancel()\n"
        "    assert order.status == 'cancelled'\n"
    ),
    find_across=_find_copy_paste_setup,
)
