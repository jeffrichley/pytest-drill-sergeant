"""The exceptions family (DS7xx): how a test expects, or hides, an exception."""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.ast_tools import (
    PYTEST_RAISES,
    calls_to,
    is_cleanup,
    is_real_assertion,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# The exception types that every error is an instance of.
_BROAD = frozenset({"Exception", "BaseException"})

_PYTEST_FAIL = frozenset({"pytest.fail"})

# pytest's helpers that end a test without failing it.
_PYTEST_SKIPPING = frozenset({"pytest.skip", "pytest.xfail"})

# What catches `pytest.fail`: its exception derives from `BaseException` only.
_CATCHES_PYTEST_FAIL = frozenset({"BaseException"})

# What catches `assert False` and `raise AssertionError`.
_CATCHES_ASSERTION = frozenset({"Exception", "BaseException", "AssertionError"})

# What an `assert` reads from a `pytest.raises` result to pin down what was caught.
_CAUGHT_READS = frozenset({"type", "value", "typename", "errisinstance", "match"})

_TryNode = ast.Try | ast.TryStar


def _expected_exception(call: ast.Call) -> ast.expr | None:
    """The exception type a `pytest.raises` call expects, if it names one."""
    if call.args:
        return call.args[0]
    return next((k.value for k in call.keywords if k.arg == "expected_exception"), None)


def _type_names(expr: ast.expr | None) -> set[str]:
    """The names of the exception types an expression gives, alone or in a tuple."""
    candidates = expr.elts if isinstance(expr, ast.Tuple) else [expr]
    return {c.id for c in candidates if isinstance(c, ast.Name)}


def _has_match(call: ast.Call) -> bool:
    """Whether a `pytest.raises` call passes a `match=` that can reject a message.

    `match=None` and `match=""` match every message, so they don't count.
    """
    return any(
        k.arg == "match"
        and not (isinstance(k.value, ast.Constant) and k.value.value in (None, ""))
        for k in call.keywords
    )


def _pins(test: ast.expr) -> bool:
    """Whether an `assert`'s test can pin a value down.

    A comparison with no `None` in it or a call can; a bare truthiness check or an
    `is not None` holds for whatever was caught.
    """
    if isinstance(test, ast.Call):
        return True
    return isinstance(test, ast.Compare) and not any(
        isinstance(operand, ast.Constant) and operand.value is None
        for operand in (test.left, *test.comparators)
    )


def _narrowed_afterwards(test: TestFunction) -> set[int]:
    """The `pytest.raises` calls in a test whose `as` name is narrowed later.

    It is when the name calls `.match(...)`, or an `assert` that can pin a value
    down reads what was caught: its `.type`, `.value`, `.typename`, or
    `.errisinstance(...)` (as in `assert excinfo.type is TypeError` or
    `assert "x" in str(excinfo.value)`, not `assert excinfo.type is not None`).

    Returns:
        The ids of those call nodes.
    """
    nodes = list(walk_test(test))
    narrowed = {
        node.func.value.id
        for node in nodes
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "match"
        and isinstance(node.func.value, ast.Name)
    } | {
        read.value.id
        for node in nodes
        if isinstance(node, ast.Assert) and _pins(node.test)
        for read in ast.walk(node.test)
        if isinstance(read, ast.Attribute)
        and read.attr in _CAUGHT_READS
        and isinstance(read.value, ast.Name)
    }
    return {
        id(item.context_expr)
        for node in nodes
        if isinstance(node, ast.With | ast.AsyncWith)
        for item in node.items
        if isinstance(item.optional_vars, ast.Name)
        and item.optional_vars.id in narrowed
    }


def _find_broad_raises(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        matched = _narrowed_afterwards(test)
        for node in walk_test(test):
            if not (
                isinstance(node, ast.Call)
                and calls_to(node, PYTEST_RAISES, test.imports)
            ):
                continue
            broad = sorted(_type_names(_expected_exception(node)) & _BROAD)
            if not broad or _has_match(node) or id(node) in matched:
                continue
            yield Hit.on(
                test,
                node.lineno,
                found=(
                    f"expects `{broad[0]}` with no `match=`, so any error at all "
                    "passes it."
                ),
                fix=(
                    f"replace `{broad[0]}` with the specific exception the code "
                    "raises, and add `match=` for the part of its message that "
                    "matters."
                ),
            )


BROAD_RAISES = Check(
    code="DS701",
    name="broad-raises",
    default_level=Level.FAIL,
    voice=(
        "Expecting `Exception`? That's not a target, recruit, that's the whole range!",
        "A typo in your own test raises too, maggot! NAME THE EXCEPTION!",
        "Any error passes this test! Even the wrong one! ESPECIALLY the wrong one!",
    ),
    why=(
        "`pytest.raises(Exception)` with no `match=` passes for any error, including "
        "a `TypeError` from a typo in the test, so it can't tell the expected failure "
        "from a broken one."
    ),
    explain=(
        "Flags `pytest.raises` expecting `Exception` or `BaseException`, alone or in "
        'a tuple, with no `match=` (or one of `None` or `""`, which match '
        "anything), no later `.match(...)` on its `as` name, and no later `assert` "
        "pinning down what it caught (`assert excinfo.type is TypeError`, `assert "
        '"x" in str(excinfo.value)`). Name the specific '
        "exception the code raises, and add `match=` for the part of its message "
        "that matters."
    ),
    bad_example=(
        "import pytest\n"
        "\n"
        "def test_bad_input():\n"
        "    with pytest.raises(Exception):\n"
        "        parse(None)\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "def test_none_input_rejected():\n"
        '    with pytest.raises(ParseError, match="must not be None"):\n'
        "        parse(None)\n"
    ),
    find=_find_broad_raises,
)


def _tries(test: TestFunction) -> Iterator[tuple[_TryNode, ast.stmt | None]]:
    """Every `try` in a test's body, with the statement that follows it, if any."""
    blocks: list[list[ast.stmt]] = [test.node.body]
    for node in walk_test(test):
        blocks.extend(
            value
            for _field, value in ast.iter_fields(node)
            if isinstance(value, list) and value and isinstance(value[0], ast.stmt)
        )
    for block in blocks:
        for index, item in enumerate(block):
            if isinstance(item, _TryNode):
                yield item, block[index + 1] if index + 1 < len(block) else None


def _caught_by(
    statement: ast.stmt | None, names: Mapping[str, str]
) -> frozenset[str] | None:
    """The handler types that catch a statement's failure, if it always fails.

    A `raise`, an `assert` of a falsy constant and a `pytest.fail` call always fail
    the test; anything else returns `None`. A bare `except` catches every failure.
    """
    if isinstance(statement, ast.Raise):
        exc = (
            statement.exc.func if isinstance(statement.exc, ast.Call) else statement.exc
        )
        return _CATCHES_ASSERTION | _type_names(exc)
    if isinstance(statement, ast.Assert):
        test = statement.test
        failing = isinstance(test, ast.Constant) and not test.value
        return _CATCHES_ASSERTION if failing else None
    if isinstance(statement, ast.Expr) and calls_to(
        statement.value, _PYTEST_FAIL, names
    ):
        return _CATCHES_PYTEST_FAIL
    return None


def _catches(handler: ast.ExceptHandler, types: frozenset[str]) -> bool:
    """Whether a handler catches any of the named types; a bare one catches all."""
    return handler.type is None or bool(_type_names(handler.type) & types)


def _expects_the_exception(
    node: _TryNode, following: ast.stmt | None, names: Mapping[str, str]
) -> bool:
    """Whether the `try` fails the test when nothing is raised.

    Then the exception is the expected outcome, and catching it is the old way to
    write `pytest.raises`: the `try` body ends in a failure no handler catches, its
    `else` holds a failure, or the statement right after it is one.
    """
    body_caught_by = _caught_by(node.body[-1], names)
    return (
        (
            body_caught_by is not None
            and not any(_catches(h, body_caught_by) for h in node.handlers)
        )
        or any(_caught_by(statement, names) is not None for statement in node.orelse)
        or _caught_by(following, names) is not None
    )


def _handles(handler: ast.ExceptHandler, names: Mapping[str, str]) -> bool:
    """Whether a handler has a real assertion or a `raise`.

    `pytest.skip` and `pytest.xfail` count too, in a handler for a specific type:
    in a bare or broad one they turn every failure into a skip.
    """
    nodes = [node for statement in handler.body for node in ast.walk(statement)]
    if any(
        is_real_assertion(node, names) or isinstance(node, ast.Raise) for node in nodes
    ):
        return True
    return not _catches(handler, _BROAD) and any(
        calls_to(node, _PYTEST_SKIPPING, names) for node in nodes
    )


def _tolerates_cleanup(
    node: _TryNode, handler: ast.ExceptHandler, names: Mapping[str, str]
) -> bool:
    """Whether the `try` is cleanup that tolerates one specific error.

    Its body only cleans up (`path.unlink()`, `os.remove(...)`), and the handler
    names a specific type, not `Exception` or `BaseException`, and only passes:
    `try: path.unlink()` / `except FileNotFoundError: pass`.
    """
    return (
        handler.type is not None
        and not _catches(handler, _BROAD)
        and all(isinstance(s, ast.Pass) for s in handler.body)
        and all(
            isinstance(s, ast.Expr)
            and isinstance(s.value, ast.Call)
            and is_cleanup(s.value, names)
            for s in node.body
        )
    )


def _find_swallowed_exception(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for node, following in _tries(test):
            if _expects_the_exception(node, following, test.imports):
                continue
            for handler in node.handlers:
                if _handles(handler, test.imports) or _tolerates_cleanup(
                    node, handler, test.imports
                ):
                    continue
                caught = (
                    f"`{ast.unparse(handler.type)}`"
                    if handler.type is not None
                    else "every exception"
                )
                yield Hit.on(
                    test,
                    handler.lineno,
                    found=(
                        f"catches {caught} in a handler with no real assertion and "
                        "no `raise`, so the error is lost."
                    ),
                    fix=(
                        f"remove the `try` that catches {caught} and let the "
                        "exception fail the test; if raising is the expected "
                        "behaviour, use `pytest.raises(..., match=...)` instead."
                    ),
                )


SWALLOWED_EXCEPTION = Check(
    code="DS702",
    name="swallowed-exception",
    default_level=Level.FAIL,
    voice=(
        "You caught the failure and HID it, recruit? That's desertion!",
        "`except: pass` isn't a test, maggot, it's a cover-up!",
        "The code blew up and your test looked the other way! EYES FRONT!",
    ),
    why=(
        "A test that catches an exception and carries on passes when the code under "
        "test breaks, so it hides exactly the failure it should report."
    ),
    explain=(
        "Flags an `except` handler in a test with no real assertion and no `raise`: "
        "one that is `pass`, `continue`, a bare `return`, or that logs and carries "
        "on. `pytest.skip` or `pytest.xfail` in a handler for a specific type counts "
        "as handling it; in a bare or broad handler it doesn't. A `try` that fails "
        "the test when nothing is raised expects the exception and is not flagged: "
        "its `else`, or the statement right after it, is `pytest.fail`, `raise` or "
        "`assert False`, or its body ends in one that no handler catches. Nor is "
        "cleanup that tolerates one specific error: a `try` whose body only cleans "
        "up (`path.unlink()`, `os.remove(...)`) with a handler that names a type "
        "other than `Exception` or `BaseException` and only passes. Let "
        "exceptions propagate, and use `pytest.raises(..., match=...)` when raising "
        "is the expected behaviour."
    ),
    bad_example=(
        "def test_sync():\n"
        "    try:\n"
        "        sync_all()\n"
        "    except Exception:\n"
        "        pass\n"
        "    assert store.pending == []\n"
    ),
    good_example=("def test_sync():\n    sync_all()\n    assert store.pending == []\n"),
    find=_find_swallowed_exception,
)
