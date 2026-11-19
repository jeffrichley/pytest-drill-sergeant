"""What a check is, and what it is given and gives back."""

import ast
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from pytest_drill_sergeant.findings import Level

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


@dataclass(frozen=True)
class TestFunction:
    """A test function as pytest would collect it, with its syntax tree.

    Attributes:
        name: The test's name, with its class path (`TestX::test_y`).
        node: The function's syntax tree.
    """

    __test__ = False  # Not a pytest test class, despite the name.

    name: str
    node: FunctionNode


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
        find: Reports the hits among one file's tests.
    """

    code: str
    name: str
    default_level: Level
    voice: tuple[str, ...]
    why: str
    explain: str
    bad_example: str
    good_example: str
    find: Callable[[Iterable[TestFunction]], Iterable[Hit]]
