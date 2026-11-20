"""The per-file summary: what cross-file analysis needs to know of one test file.

A test's setup is its leading statements, before the first one that holds a real
assertion; a docstring is not one of them. Each statement is recorded by its
fingerprint, so two statements that read the same, wherever they stand, compare
equal, and a different name or literal makes them differ. A test's whole body is
recorded by its fingerprint and by its shape, the fingerprint with every name and
literal blanked, with the names and the literals that shape blanked, in order, so
tests of one shape can be told apart by them; its `def` line and decorators are
recorded by their fingerprint. The summary is plain data, the same for the same
file bytes.
"""

import ast
import copy
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


def _blanked(statement: ast.stmt) -> ast.stmt:
    """A copy of a statement with every name and literal blanked."""
    blank = copy.deepcopy(statement)
    for node in ast.walk(blank):
        if isinstance(node, ast.Name):
            node.id = "_"
        elif isinstance(node, ast.arg):
            node.arg = "_"
        elif isinstance(node, ast.Constant):
            node.value = None
    return blank


def shape(nodes: list[ast.stmt]) -> str:
    """The fingerprint of statements with every name and literal blanked.

    Statements that differ only in their names and values share a shape.
    """
    return fingerprint([_blanked(node) for node in nodes])


def _is_signed_literal(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub | ast.UAdd)
        and isinstance(node.operand, ast.Constant)
    )


def _blanked_leaves(node: ast.AST, names: list[str], literals: list[str]) -> None:
    """Collect, in source order, the names and literals a shape blanks.

    A signed literal (`-1`) is one literal, as it reads.
    """
    if isinstance(node, ast.Name):
        names.append(node.id)
    elif isinstance(node, ast.arg):
        names.append(node.arg)
    if isinstance(node, ast.Constant) or _is_signed_literal(node):
        literals.append(ast.unparse(node))
        return
    for child in ast.iter_child_nodes(node):
        _blanked_leaves(child, names, literals)


def _signature(test: TestFunction) -> str:
    """The fingerprint of a test's `def` line and decorators, blind to its name."""
    head = copy.copy(test.node)
    head.name = "_"
    head.body = []
    return fingerprint([head])


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
    names: list[str] = []
    literals: list[str] = []
    for statement in body:
        _blanked_leaves(statement, names, literals)
    return TestSummary(
        name=test.name,
        line=test.node.lineno,
        setup=tuple(setup),
        body=fingerprint(body),
        shape=shape(body),
        names=tuple(names),
        literals=tuple(literals),
        signature=_signature(test),
    )


def summarize(file: TestFile) -> FileSummary:
    """The per-file summary of a test file: each test's setup and body."""
    return FileSummary(tests=tuple(_summarize_test(test) for test in file.tests))
