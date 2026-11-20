"""What a check is, and what it is given and gives back.

A check reads one test file at a time, or compares the per-file summaries of every
file in the run (cross-file analysis), or both. A summary is plain data, so the
cross-file step never needs a file's syntax tree.

A test's own code, for every check, is its whole body: a helper function, class or
lambda defined inside a test is part of it, so an assertion or a call there counts
(`ast_tools.walk_test`). Only the act-and-assert order (DS103, DS104) reads the
body's statements one by one, and there a nested `def` only defines its helper.
"""

import ast
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.findings import Level
from pytest_drill_sergeant.waivers import Waiver

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class TestFunction:
    """A test function as pytest would collect it, with its syntax tree.

    Attributes:
        name: The test's name, with its class path (`TestX::test_y`).
        node: The function's syntax tree.
        imports: The imported names the test sees, each with what it stands for
            in full (`pt` is `pytest` after `import pytest as pt`).
    """

    __test__ = False  # Not a pytest test class, despite the name.

    name: str
    node: FunctionNode
    imports: Mapping[str, str]


@dataclass(frozen=True)
class Thresholds:
    """The configured thresholds a check may measure one file against.

    Attributes:
        max_file_lines: The most lines a test file may have.
        max_test_lines: The most lines a test function may have.
        max_mock_setup: The most mock-setup statements a test may have.
        duplicate_setup_min_statements: The fewest statements a copy-pasted setup
            block has.
        duplicate_setup_min_tests: The fewest tests a copy-pasted setup block is in.
    """

    max_file_lines: int = 500
    max_test_lines: int = 50
    max_mock_setup: int = 10
    duplicate_setup_min_statements: int = 3
    duplicate_setup_min_tests: int = 3


@dataclass(frozen=True)
class TestFile:
    """One parsed test file: what every check is given.

    Attributes:
        path: The file, as it was given to the engine.
        module: The file's syntax tree, for checks that need more than the tests
            (imports, module-level code).
        tests: The tests pytest would collect from it, in source order.
        waivers: Its `# drill: waive` comments, complete or not; none when inline
            waivers are off.
        thresholds: The configured thresholds, for checks that measure.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    path: Path
    module: ast.Module
    tests: tuple[TestFunction, ...]
    waivers: tuple[Waiver, ...] = ()
    thresholds: Thresholds = Thresholds()


@dataclass(frozen=True)
class Statement:
    """One statement of a test, as a per-file summary records it.

    Attributes:
        fingerprint: The statement's fingerprint.
        line: The line it starts on.
        end_line: The line it ends on.
        binds: The names it binds, in order.
    """

    fingerprint: str
    line: int
    end_line: int
    binds: tuple[str, ...] = ()


@dataclass(frozen=True)
class TestSummary:
    """One test, as a per-file summary records it.

    Attributes:
        name: The test's name, with its class path (`TestX::test_y`).
        line: The line its `def` is on.
        setup: Its setup statements, in order.
        body: The fingerprint of its whole body.
        shape: Its whole body's shape: the fingerprint with every name and
            literal blanked, alike for tests that differ only in their values.
        names: The names its shape blanks, in source order.
        literals: The literals its shape blanks, each as it reads in source
            (`'apple'`, `-1`), in source order.
        signature: The fingerprint of its `def` line (parameters, `async`) and
            decorators, blind to its name.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    name: str
    line: int
    setup: tuple[Statement, ...]
    body: str
    shape: str
    names: tuple[str, ...]
    literals: tuple[str, ...]
    signature: str


@dataclass(frozen=True)
class FileSummary:
    """A per-file summary: what cross-file analysis knows of one test file.

    Attributes:
        tests: Each test pytest would collect from the file, in source order.
    """

    tests: tuple[TestSummary, ...] = ()


@dataclass(frozen=True)
class Hit:
    """What a check reports about one test, before the engine makes it a finding.

    Attributes:
        line: The line to report.
        test: The test's name.
        found: What the check found, in plain words.
        fix: How to fix it, naming the specifics where the check knows them.
    """

    line: int
    test: str
    found: str
    fix: str

    @classmethod
    def on(cls, test: TestFunction, line: int, *, found: str, fix: str) -> "Hit":
        """A hit on a line of a test, in the phrasing every check shares.

        `found` follows "`<test>` " and `fix` follows "In `<test>`, line <n>: ",
        so every finding names its test first and every fix says where to look.
        """
        return cls.at(test.name, line, found=found, fix=fix)

    @classmethod
    def at(cls, test: str, line: int, *, found: str, fix: str) -> "Hit":
        """A hit on a line of the test named `test`, phrased as `on` phrases it."""
        return cls(
            line=line,
            test=test,
            found=f"`{test}` {found}",
            fix=f"In `{test}`, line {line}: {fix}",
        )


def and_list(items: Sequence[str]) -> str:
    """Items as a sentence list: `a`, `a and b`, `a, b and c`."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


# The files a cross-file check compares, each as given to the engine with its
# summary, ordered by path.
Summaries = Sequence[tuple[Path, FileSummary]]


def _finds_nothing(_file: TestFile) -> Iterable[Hit]:
    return ()


def _compares_nothing(
    _summaries: Summaries, _thresholds: Thresholds
) -> Iterable[tuple[Path, Hit]]:
    return ()


@dataclass(frozen=True)
class Check:
    """One deterministic detection of a single failure mode.

    Attributes:
        code: The permanent `DS###` code, numbered by family; never reused.
        name: The kebab-case name.
        default_level: The level its findings have unless configured otherwise.
        voice: About three lines in the drill-sergeant voice, one picked per finding.
        why: Why the failure mode matters, the same for every finding.
        explain: What the check flags and how to fix it, for `explain`.
        bad_example: A test the check flags.
        good_example: The same test, fixed.
        find: Reports the hits in one test file.
        find_across: Reports the hits that comparing every file's summary turns
            up, each with the file it is in.
    """

    code: str
    name: str
    default_level: Level
    voice: tuple[str, ...]
    why: str
    explain: str
    bad_example: str
    good_example: str
    find: Callable[[TestFile], Iterable[Hit]] = _finds_nothing
    find_across: Callable[[Summaries, Thresholds], Iterable[tuple[Path, Hit]]] = (
        _compares_nothing
    )
