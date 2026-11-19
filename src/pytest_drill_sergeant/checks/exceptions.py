"""The exceptions family (DS7xx): how a test expects, or hides, an exception."""

import ast
from collections.abc import Iterator

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.checks.structure import is_real_assertion
from pytest_drill_sergeant.findings import Level

# The exception types that every error is an instance of.
_BROAD = frozenset({"Exception", "BaseException"})

# pytest's helpers that end the test by raising, so a handler calling one hides
# nothing.
_PYTEST_ENDING = frozenset({"fail", "skip", "xfail"})

TryNode = ast.Try | ast.TryStar


def _is_pytest_raises(func: ast.expr) -> bool:
    """Whether a call target is `pytest.raises`, called as such or by its bare name."""
    if isinstance(func, ast.Attribute):
        return (
            isinstance(func.value, ast.Name)
            and func.value.id == "pytest"
            and func.attr == "raises"
        )
    return isinstance(func, ast.Name) and func.id == "raises"


def _expected_exception(call: ast.Call) -> ast.expr | None:
    """The exception type a `pytest.raises` call expects, if it names one."""
    if call.args:
        return call.args[0]
    return next((k.value for k in call.keywords if k.arg == "expected_exception"), None)


def _broad_name(expected: ast.expr | None) -> str | None:
    """The broad type an expected exception names, alone or in a tuple."""
    candidates = expected.elts if isinstance(expected, ast.Tuple) else [expected]
    return next(
        (c.id for c in candidates if isinstance(c, ast.Name) and c.id in _BROAD),
        None,
    )


def _has_match(call: ast.Call) -> bool:
    """Whether a `pytest.raises` call passes a `match=` that isn't `None`."""
    return any(
        k.arg == "match"
        and not (isinstance(k.value, ast.Constant) and k.value.value is None)
        for k in call.keywords
    )


def _find_broad_raises(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for statement in test.node.body:
            for node in ast.walk(statement):
                if not (isinstance(node, ast.Call) and _is_pytest_raises(node.func)):
                    continue
                broad = _broad_name(_expected_exception(node))
                if broad is None or _has_match(node):
                    continue
                yield Hit(
                    line=node.lineno,
                    test=test.name,
                    found=(
                        f"`{test.name}` expects `{broad}` with no `match=` on line "
                        f"{node.lineno}, so any error at all passes it."
                    ),
                    fix=(
                        f"On line {node.lineno} of `{test.name}`, replace `{broad}` "
                        "with the specific exception the code raises, and add "
                        "`match=` for the part of its message that matters."
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
        "a tuple, with no `match=`. Name the specific exception the code raises, and "
        "add `match=` for the part of its message that matters."
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


def _tries(test: TestFunction) -> Iterator[tuple[TryNode, ast.stmt | None]]:
    """Every `try` in a test, with the statement that follows it, if any."""
    for node in ast.walk(test.node):
        for _field, value in ast.iter_fields(node):
            if not isinstance(value, list):
                continue
            for index, item in enumerate(value):
                if isinstance(item, TryNode):
                    following = value[index + 1] if index + 1 < len(value) else None
                    yield item, following


def _is_pytest_ending(node: ast.AST) -> bool:
    """Whether a node calls `pytest.fail`, `pytest.skip` or `pytest.xfail`."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pytest"
        and node.func.attr in _PYTEST_ENDING
    )


def _always_fails(statement: ast.stmt | None) -> bool:
    """Whether a statement fails the test whenever it runs.

    A `raise`, an `assert` of a falsy constant and a `pytest.fail` call do.
    """
    if isinstance(statement, ast.Raise):
        return True
    if isinstance(statement, ast.Assert):
        test = statement.test
        return isinstance(test, ast.Constant) and not test.value
    return isinstance(statement, ast.Expr) and _is_pytest_ending(statement.value)


def _expects_the_exception(node: TryNode, following: ast.stmt | None) -> bool:
    """Whether the `try` fails the test when nothing is raised.

    Then the exception is the expected outcome, and catching it is the old way to
    write `pytest.raises`: the `try` body ends in a failure, its `else` holds one,
    or the statement right after it is one.
    """
    return (
        _always_fails(node.body[-1])
        or any(_always_fails(statement) for statement in node.orelse)
        or _always_fails(following)
    )


def _handles(handler: ast.ExceptHandler) -> bool:
    """Whether an `except` handler asserts on the exception or raises again."""
    return any(
        is_real_assertion(node)
        or isinstance(node, ast.Raise)
        or _is_pytest_ending(node)
        for statement in handler.body
        for node in ast.walk(statement)
    )


def _find_swallowed_exception(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for node, following in _tries(test):
            if _expects_the_exception(node, following):
                continue
            for handler in node.handlers:
                if _handles(handler):
                    continue
                caught = (
                    f"`{ast.unparse(handler.type)}`"
                    if handler.type is not None
                    else "every exception"
                )
                yield Hit(
                    line=handler.lineno,
                    test=test.name,
                    found=(
                        f"`{test.name}` catches {caught} on line {handler.lineno} "
                        "and neither asserts on it nor raises it again."
                    ),
                    fix=(
                        f"In `{test.name}`, remove the `try` that catches {caught} on "
                        f"line {handler.lineno} and let the exception fail the test; "
                        "if raising is the expected behaviour, use "
                        "`pytest.raises(..., match=...)` instead."
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
        "Flags an `except` handler in a test that neither has a real assertion nor "
        "raises (re-raising, `pytest.fail`, `pytest.skip` and `pytest.xfail` count): "
        "a handler that is `pass`, `continue`, a bare `return`, or that logs and "
        "carries on. A `try` that fails the test when nothing is raised (its body "
        "ends in, its `else` holds, or it is followed by `pytest.fail`, `raise` or "
        "`assert False`) expects the exception, and is not flagged. Let exceptions "
        "propagate, and use `pytest.raises(..., match=...)` when raising is the "
        "expected behaviour."
    ),
    bad_example=(
        "def test_sync():\n"
        "    try:\n"
        "        sync_all()\n"
        "    except Exception:\n"
        "        pass\n"
        "    assert store.synced\n"
    ),
    good_example=("def test_sync():\n    sync_all()\n    assert store.synced\n"),
    find=_find_swallowed_exception,
)
