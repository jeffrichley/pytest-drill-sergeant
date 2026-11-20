"""The per-file summary: what cross-file analysis needs to know of one test file.

A test's setup is its leading statements, before the first one that holds a real
assertion; a docstring is not one of them. Each statement is recorded by its
fingerprint, so two statements that read the same, wherever they stand, compare
equal, and a different name or literal makes them differ. The summary is plain
data, the same for the same file bytes.
"""

import ast
import hashlib

from pytest_drill_sergeant.checks.ast_tools import bound_names, is_real_assertion
from pytest_drill_sergeant.checks.base import (
    FileSummary,
    Statement,
    TestFile,
    TestFunction,
    TestSummary,
)


def fingerprint(nodes: list[ast.stmt]) -> str:
    """A stable digest of what statements say, blind to where they stand.

    Comments, layout and line numbers don't change it; any name, literal or
    structure does.
    """
    text = "\n".join(ast.dump(node) for node in nodes)
    return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _asserts(statement: ast.stmt, test: TestFunction) -> bool:
    return any(is_real_assertion(node, test.imports) for node in ast.walk(statement))


def _summarize_test(test: TestFunction) -> TestSummary:
    body = [s for s in test.node.body if not _is_docstring(s)]
    setup: list[Statement] = []
    for statement in body:
        if _asserts(statement, test):
            break
        setup.append(
            Statement(
                fingerprint=fingerprint([statement]),
                line=statement.lineno,
                end_line=statement.end_lineno or statement.lineno,
                binds=tuple(bound_names(statement)),
            )
        )
    return TestSummary(
        name=test.name,
        line=test.node.lineno,
        setup=tuple(setup),
        body=fingerprint(body),
    )


def summarize(file: TestFile) -> FileSummary:
    """The per-file summary of a test file: each test's setup and body."""
    return FileSummary(tests=tuple(_summarize_test(test) for test in file.tests))
