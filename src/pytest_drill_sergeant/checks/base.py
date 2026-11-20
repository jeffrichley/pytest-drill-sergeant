"""What a check is, and what it is given and gives back.

A test's own code, for every check, is its whole body: a helper function, class or
lambda defined inside a test is part of it, so an assertion or a call there counts
(`ast_tools.walk_test`). Only the act-and-assert order (DS103, DS104) reads the
body's statements one by one, and there a nested `def` only defines its helper.
"""

import ast
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from pytest_drill_sergeant.findings import Level

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
    """

    max_file_lines: int = 500
    max_test_lines: int = 50
    max_mock_setup: int = 10


@dataclass(frozen=True)
class TestFile:
    """One parsed test file: what every check is given.

    Attributes:
        path: The file, as it was given to the engine.
        module: The file's syntax tree, for checks that need more than the tests
            (imports, module-level code).
        tests: The tests pytest would collect from it, in source order.
        thresholds: The configured thresholds, for checks that measure.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    path: Path
    module: ast.Module
    tests: tuple[TestFunction, ...]
    thresholds: Thresholds = Thresholds()


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
        return cls(
            line=line,
            test=test.name,
            found=f"`{test.name}` {found}",
            fix=f"In `{test.name}`, line {line}: {fix}",
        )


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
    """

    code: str
    name: str
    default_level: Level
    voice: tuple[str, ...]
    why: str
    explain: str
    bad_example: str
    good_example: str
    find: Callable[[TestFile], Iterable[Hit]]
