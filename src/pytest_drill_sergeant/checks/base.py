"""What a check is, and what it is given and gives back.

A check reads one test file at a time, or compares the per-file summaries of every
file in the run (cross-file analysis), or both. A summary is plain data, so the
cross-file step never needs a file's syntax tree.

A test's own code, for every check, is its whole body: a helper function, class or
lambda defined inside a test is part of it, so an assertion or a call there counts
(`ast_tools.walk_test`). Only the act-and-assert order (DS103, DS104, DS108) reads the
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
        classes: The classes it is defined in, outermost first; none for a test
            at module level.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    name: str
    node: FunctionNode
    imports: Mapping[str, str]
    classes: tuple[ast.ClassDef, ...] = ()


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
class Comment:
    """A comment alone on its line, as `tokenize` reads it, so never text in a string.

    Attributes:
        line: The line it is on.
        text: The comment, `#` included.
    """

    line: int
    text: str


@dataclass(frozen=True)
class TestFile:
    """One parsed test file: what every check is given.

    Attributes:
        path: The file, as it was given to the engine.
        module: The file's syntax tree, for checks that need more than the tests
            (imports, module-level code).
        tests: The tests pytest would collect from it, in source order.
        lines: How many lines the file has.
        waivers: Its `# drill: waive` comments, complete or not; none when inline
            waivers are off.
        thresholds: The configured thresholds, for checks that measure.
        category_markers: The configured category markers.
        directories: The names of the directories the file is in, outermost
            first, from its path relative to the config root (or as given, when it
            is outside the root).
        comments: Its comments that stand alone on their lines, in line order.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    path: Path
    module: ast.Module
    tests: tuple[TestFunction, ...]
    lines: int
    waivers: tuple[Waiver, ...] = ()
    thresholds: Thresholds = Thresholds()
    category_markers: tuple[str, ...] = ("unit", "integration", "e2e")
    directories: tuple[str, ...] = ()
    comments: tuple[Comment, ...] = ()


@dataclass(frozen=True)
class SourceFile:
    """One parsed file of production code: what a check that reads it is given.

    Attributes:
        path: The file, as it was given to the engine.
        module: The file's syntax tree.
    """

    path: Path
    module: ast.Module


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
    """What a check reports, before the engine makes it a finding.

    A hit is about one test, or about the whole file (a file too long).

    Attributes:
        line: The line to report.
        test: The test's name, or empty for a hit about the whole file.
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
    def at(cls, where: str, line: int, *, found: str, fix: str) -> "Hit":
        """A hit on a line of a named place: a test, a class, a function or `<module>`.

        The phrasing is `on`'s, with the place's name where the test's would be.
        """
        return cls(
            line=line,
            test=where,
            found=f"`{where}` {found}",
            fix=f"In `{where}`, line {line}: {fix}",
        )

    @classmethod
    def on_file(cls, file: "TestFile", *, found: str, fix: str) -> "Hit":
        """A hit about a whole file, reported on its first line.

        `found` follows "`<file name>` " and `fix` follows "In `<file name>`: ",
        the file standing where a test's name would.
        """
        return cls(
            line=1,
            test="",
            found=f"`{file.path.name}` {found}",
            fix=f"In `{file.path.name}`: {fix}",
        )


def and_list(items: Sequence[str]) -> str:
    """Items as a sentence list: `a`, `a and b`, `a, b and c`."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


# The files a cross-file check compares, each as given to the engine with its
# summary, ordered by path.
Summaries = Sequence[tuple[Path, FileSummary]]

# Whether a check reports in a file, as `reports(code, path)`: the check is not
# `off` there, by its level or a per-file ignore.
Reports = Callable[[str, Path], bool]

# What a cross-file check is given: every file's summary, the thresholds, and
# whether another check reports in a file, for a check that defers to it.
FindAcross = Callable[[Summaries, Thresholds, Reports], Iterable[tuple[Path, Hit]]]


def _finds_nothing(_file: TestFile) -> Iterable[Hit]:
    return ()


def _compares_nothing(
    _summaries: Summaries, _thresholds: Thresholds, _reports: Reports
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
        find: Reports the hits in one test file; by default, none.
        find_in_source: Reports the hits in one file of production code; `None`
            for a check that reads only test files. Which files a check reads is
            which of the two it gives: DS403 gives only this one.
        find_across: Reports the hits that comparing every file's summary turns
            up, each with the file it is in; it is told which checks report in
            which files, so it can leave a problem to a more specific check.
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
    find_in_source: Callable[[SourceFile], Iterable[Hit]] | None = None
    find_across: FindAcross = _compares_nothing

    @property
    def compares_files(self) -> bool:
        """Whether the check compares files' summaries, not only reads files."""
        return self.find_across is not _compares_nothing
