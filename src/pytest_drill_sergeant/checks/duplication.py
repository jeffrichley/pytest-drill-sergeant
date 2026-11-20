"""The duplication family (DS5xx): tests that repeat what one place should hold.

Its checks compare per-file summaries across every file in the run, never the files
themselves (cross-file analysis), so a block pasted into tests in different files
is caught as surely as one pasted within a file.

Near-duplicate tests (DS502) are tests of one file and one class, alike in their
`def` line, decorators and every name, and differing at most in their body's
literals: one parametrized test holds them all. Parametrizing them takes their
shared setup with them, so copy-pasted setup (DS501) counts each such group as one
test, its first, in a file where DS502 reports.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.checks.ast_tools import TEST_PATH
from pytest_drill_sergeant.checks.base import (
    Check,
    Hit,
    Kind,
    Reports,
    Statement,
    Summaries,
    TestSummary,
    Thresholds,
    and_list,
)
from pytest_drill_sergeant.findings import Level

# The near-duplicate check's code: copy-pasted setup leaves its groups to it.
_NEAR_DUPLICATE_TESTS = "DS502"


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


def _near_duplicates(
    summaries: Summaries,
) -> Iterator[tuple[Path, list[TestSummary]]]:
    """Each group of near-duplicate tests, with its file, its tests in source order.

    A group is two tests or more of one file and one class, alike in their `def`
    line and decorators, and in their body's shape and every name in it.
    """
    for path, summary in summaries:
        groups: dict[tuple[object, ...], list[TestSummary]] = {}
        for test in summary.tests:
            scope = test.name.rpartition(TEST_PATH)[0]
            key = (scope, test.signature, test.shape, test.names)
            groups.setdefault(key, []).append(test)
        for tests in groups.values():
            if len(tests) > 1:
                yield path, tests


def _setups(summaries: Summaries, reports: Reports) -> list[_Setup]:
    """Every test's setup, a group of near-duplicate tests counted as its first.

    A group is folded only in a file where the near-duplicate check reports it.
    """
    folded = {
        (path, test.name)
        for path, tests in _near_duplicates(summaries)
        if reports(_NEAR_DUPLICATE_TESTS, path)
        for test in tests[1:]
    }
    return [
        _Setup(path=path, test=test.name, statements=test.setup)
        for path, summary in summaries
        for test in summary.tests
        if (path, test.name) not in folded
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


def _block_length(copies: list[_Copy], size: int) -> int:
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
    """The fixture to suggest: named for the last public name the block binds."""
    names = [
        name
        for statement in block
        for name in statement.binds
        if not name.startswith("_")
    ]
    return f"a fixture, e.g. `{names[-1]}`," if names else "a fixture"


def _find_copy_paste_setup(
    summaries: Summaries, thresholds: Thresholds, reports: Reports
) -> Iterator[tuple[Path, Hit]]:
    # A block is at least one statement, and is pasted only if two tests hold it.
    size = max(thresholds.duplicate_setup_min_statements, 1)
    min_tests = max(thresholds.duplicate_setup_min_tests, 2)
    # A statement is reported in one block at most: a block that overlaps one
    # already reported, in any test, waits for that one's fixture.
    reported: set[tuple[int, int]] = set()  # (setup id, statement index)
    for copies in _windows(_setups(summaries, reports), size).values():
        if len(copies) < min_tests:
            continue
        length = _block_length(copies, size)
        spans = [{(id(c.setup), c.start + i) for i in range(length)} for c in copies]
        if any(span & reported for span in spans):
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
                    f"{len(others)} other test{'s' if len(others) > 1 else ''}, "
                    "alike in every name and literal."
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
    kind=Kind.SMELL,
    default_level=Level.OFF,
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
        "statements in a row (3 by default; at least 1), alike in every name and "
        "literal, in at least `drill_sergeant_duplicate_setup_min_tests` tests (3 by "
        "default; at least 2). A "
        "test's setup is its statements before the first one that holds a real "
        "assertion. One finding per block, on its first occurrence, names the other "
        "tests that hold it; a statement is reported in one block at most, so a "
        "block overlapping one already reported shows up once that one is fixed. Setup that differs in a value is not a copy: if the "
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


_LONGEST_LITERAL = 30


def _shown(literal: str) -> str:
    """A literal as the fix shows it: a long one cut short, its closing quote kept."""
    if len(literal) <= _LONGEST_LITERAL:
        return literal
    end = literal[-1] if literal[-1] in "'\"" else ""
    return f"{literal[: _LONGEST_LITERAL - 4]}...{end}"


def _parameters(tests: Sequence[TestSummary]) -> list[tuple[str, ...]]:
    """The literals that differ between the tests, one tuple per test.

    Literals that vary together (each test repeating its own value) are one
    parameter.
    """
    columns = dict.fromkeys(zip(*(test.literals for test in tests), strict=True))
    varying = [column for column in columns if len(set(column)) > 1]
    return list(zip(*varying, strict=True))


def _parametrize(rows: list[tuple[str, ...]]) -> str:
    if len(rows[0]) == 1:
        values = ", ".join(_shown(row[0]) for row in rows)
        return f'@pytest.mark.parametrize("value", [{values}])'
    names = ", ".join(f'"value_{n}"' for n in range(1, len(rows[0]) + 1))
    values = ", ".join(f"({', '.join(_shown(v) for v in row)})" for row in rows)
    return f"@pytest.mark.parametrize(({names}), [{values}])"


def _find_near_duplicate_tests(
    summaries: Summaries, _thresholds: Thresholds, _reports: Reports
) -> Iterator[tuple[Path, Hit]]:
    for path, tests in _near_duplicates(summaries):
        first, others = tests[0], tests[1:]
        named = and_list([f"`{t.name}` (line {t.line})" for t in others])
        count = f"{len(others)} other test{'s' if len(others) > 1 else ''}"
        rows = _parameters(tests)
        if rows:
            found = f"and {count} in its file differ only in their literals: {named}."
            fix = (
                f"merge it with {named} into one test, with the literals that "
                f"differ as parameters: `{_parametrize(rows)}`."
            )
        else:
            found = (
                f"is a copy of {count} in its file, alike in every name and "
                f"literal: {named}."
            )
            fix = f"keep this test and delete {named}."
        yield path, Hit.at(first.name, first.line, found=found, fix=fix)


NEAR_DUPLICATE_TESTS = Check(
    code=_NEAR_DUPLICATE_TESTS,
    name="near-duplicate-tests",
    kind=Kind.SMELL,
    default_level=Level.WARN,
    voice=(
        "Same test, different numbers! You think I can't SEE that, recruit?",
        "One test in a fresh coat of paint is still ONE test, maggot! Parametrize it!",
        "You copied the drill and changed the count! That's a table, not a new drill!",
    ),
    why=(
        "Tests that differ only in their values multiply the code to read and "
        "change, drift apart copy by copy, and hide the one table of cases they "
        "really are."
    ),
    explain=(
        "Flags two or more tests of one file, and of one class if they are in one, "
        "that are alike in their parameters, decorators, every name and statement, "
        "and differ at most in their body's literals; a signed number (`-1`) counts "
        "as one literal. One finding, on the "
        "first test, names the others and shows a `pytest.mark.parametrize` holding "
        "the literals that differ, one row per test; tests alike in every literal "
        "too are copies, and all but one can go. Not flagged: tests in different "
        "files or classes (one function can't hold them without moving them), "
        "tests that differ in a name, such as the function they call, or in any "
        "statement, and tests that differ in their parameters or decorators, a "
        "decorator's literals included, which a new `parametrize` can't reach; so "
        "tests already parametrized are flagged only under the very same "
        "`parametrize`. Copy-pasted setup "
        "(DS501) counts a group of near-duplicate tests as one test, since "
        "parametrizing them removes their shared setup too; with this check off "
        "for a file, DS501 counts each of them."
    ),
    bad_example=(
        "def test_one_apple_costs_three():\n"
        "    cart = Cart()\n"
        "    cart.add('apple', quantity=1)\n"
        "    assert cart.total() == 3\n"
        "\n"
        "\n"
        "def test_two_pears_cost_eight():\n"
        "    cart = Cart()\n"
        "    cart.add('pear', quantity=2)\n"
        "    assert cart.total() == 8\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "\n"
        "@pytest.mark.parametrize(\n"
        "    ('fruit', 'quantity', 'total'), [('apple', 1, 3), ('pear', 2, 8)]\n"
        ")\n"
        "def test_cart_total_prices_each_fruit(fruit, quantity, total):\n"
        "    cart = Cart()\n"
        "    cart.add(fruit, quantity=quantity)\n"
        "    assert cart.total() == total\n"
    ),
    find_across=_find_near_duplicate_tests,
)
