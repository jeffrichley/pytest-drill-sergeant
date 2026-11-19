"""The engine: test files and a config in, findings out, with no pytest in sight."""

import ast
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from pytest_drill_sergeant.checks import CHECKS, TestFile, TestFunction
from pytest_drill_sergeant.checks.base import FunctionNode
from pytest_drill_sergeant.findings import Finding, Level


@dataclass(frozen=True)
class Config:
    """The resolved configuration the engine runs with.

    Attributes:
        levels: A level per check code, overriding the check's default.
    """

    levels: Mapping[str, Level] = field(default_factory=dict)


def _is_fixture(node: FunctionNode) -> bool:
    """Whether a function is a pytest fixture, which pytest never collects as a test."""
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = target.attr if isinstance(target, ast.Attribute) else None
        if isinstance(target, ast.Name):
            name = target.id
        if name == "fixture":
            return True
    return False


def _is_collected_class(node: ast.ClassDef) -> bool:
    """Whether pytest collects a class.

    It does when the class is named `Test*`, has no `__init__` and isn't opted out
    with `__test__ = False`.
    """
    if not node.name.startswith("Test"):
        return False
    for statement in node.body:
        if isinstance(statement, ast.FunctionDef) and statement.name == "__init__":
            return False
        if (
            isinstance(statement, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "__test__"
                for t in statement.targets
            )
            and isinstance(statement.value, ast.Constant)
            and not statement.value.value
        ):
            return False
    return True


def _tests_in(body: list[ast.stmt], prefix: str = "") -> Iterator[TestFunction]:
    """The tests pytest's default rules collect.

    Those are `test*` functions that aren't fixtures, at module level or in the
    classes pytest collects, nested ones included.
    """
    for node in body:
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and node.name.startswith("test")
            and not _is_fixture(node)
        ):
            yield TestFunction(name=f"{prefix}{node.name}", node=node)
        elif isinstance(node, ast.ClassDef) and _is_collected_class(node):
            yield from _tests_in(node.body, f"{prefix}{node.name}::")


def analyze(paths: Iterable[Path], config: Config) -> list[Finding]:
    """Run every check over the test files and return the findings.

    Args:
        paths: The test files to analyse.
        config: The resolved configuration.

    Returns:
        The findings, ordered by file, line and code. Checks configured `off`
        report none.
    """
    findings: list[Finding] = []
    for path in paths:
        module = ast.parse(path.read_bytes(), filename=str(path))
        file = TestFile(path=path, module=module, tests=tuple(_tests_in(module.body)))
        for check in CHECKS:
            level = config.levels.get(check.code, check.default_level)
            if level is Level.OFF:
                continue
            findings.extend(
                Finding(
                    code=check.code,
                    name=check.name,
                    file=path,
                    line=hit.line,
                    test=hit.test,
                    level=level,
                    found=hit.found,
                    why=check.why,
                    fix=hit.fix,
                )
                for hit in check.find(file)
            )
    return sorted(findings, key=lambda f: (f.file.as_posix(), f.line, f.code))
