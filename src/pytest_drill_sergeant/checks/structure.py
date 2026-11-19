"""The structure family (DS1xx): how a test is put together."""

import ast
from collections.abc import Iterator

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# pytest's helpers that fail the test: `pytest.fail`, and the context managers that
# require an exception or warning.
_PYTEST_ASSERTING = frozenset({"fail", "raises", "warns", "deprecated_call"})


def _is_pytest_asserting(func: ast.expr) -> bool:
    """Whether a call target is one of pytest's failing helpers.

    It counts called as `pytest.<name>` or by its imported bare name.
    """
    if isinstance(func, ast.Attribute):
        return (
            isinstance(func.value, ast.Name)
            and func.value.id == "pytest"
            and func.attr in _PYTEST_ASSERTING
        )
    return isinstance(func, ast.Name) and func.id in _PYTEST_ASSERTING


def _is_always_true(test: ast.expr) -> bool:
    """Whether an `assert`'s test is a truthy constant or a non-empty tuple."""
    if isinstance(test, ast.Constant):
        return bool(test.value)
    return isinstance(test, ast.Tuple) and bool(test.elts)


def _is_real_assertion(node: ast.AST) -> bool:
    """Whether a node can fail the test on the outcome it checks.

    An `assert` of anything but a truthy constant or non-empty tuple counts, and so
    does a call to `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or
    `pytest.fail`, any `assert*`-named call (mock verification, unittest, helpers
    like `assert_frame_equal`) and raising `AssertionError`.
    """
    if isinstance(node, ast.Assert):
        return not _is_always_true(node.test)
    if isinstance(node, ast.Call):
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else None
        if isinstance(func, ast.Name):
            name = func.id
        return _is_pytest_asserting(func) or (
            name is not None and name.lower().startswith("assert")
        )
    if isinstance(node, ast.Raise) and node.exc is not None:
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        return isinstance(exc, ast.Name) and exc.id == "AssertionError"
    return False


def _last_call(test: TestFunction) -> ast.Call | None:
    """The call the test's last statement makes, if it makes one."""
    last = test.node.body[-1]
    value = last.value if isinstance(last, ast.Expr | ast.Assign) else None
    if isinstance(value, ast.Await):
        value = value.value
    return value if isinstance(value, ast.Call) else None


def _find_no_real_assertion(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        if any(
            _is_real_assertion(node)
            for statement in test.node.body
            for node in ast.walk(statement)
        ):
            continue
        call = _last_call(test)
        target = (
            f"what `{ast.unparse(call.func)}(...)` returns or changes"
            if call is not None
            else "what the code under test returns or changes"
        )
        yield Hit(
            line=test.node.lineno,
            test=test.name,
            found=(
                f"`{test.name}` has no real assertion: no `assert` that can fail, "
                "no `pytest.raises`, no mock verification."
            ),
            fix=(
                f"In `{test.name}`, assert on {target}, or wrap the call in "
                "`pytest.raises(..., match=...)` if it should raise."
            ),
        )


NO_REAL_ASSERTION = Check(
    code="DS101",
    name="no-real-assertion",
    default_level=Level.FAIL,
    voice=(
        "You call that a test, recruit? It runs the code and checks NOTHING!",
        "No assertion, no proof! Green means nothing if it can't go red, maggot!",
        "This test would pass if the code returned garbage! DROP AND GIVE ME AN ASSERT!",
    ),
    why=(
        "A test with no real assertion passes whenever the code doesn't crash, so it "
        "stays green when the behaviour breaks."
    ),
    explain=(
        "Flags a test with no real assertion: no `assert` that can fail (a truthy "
        "constant such as `assert True`, or a non-empty tuple, can't), no "
        "`pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or `pytest.fail`, "
        "no `assert*` call such as a mock's `assert_called_once_with` "
        "or `self.assertEqual`, and no `raise AssertionError`. Such a test only proves "
        "the code didn't crash. Assert on what the code returns or changes."
    ),
    bad_example=(
        "def test_process_payment():\n"
        "    handler = PaymentHandler(gateway=FakeGateway())\n"
        "    handler.process(amount=100)\n"
    ),
    good_example=(
        "def test_process_payment_records_a_charge():\n"
        "    gateway = FakeGateway()\n"
        "    PaymentHandler(gateway=gateway).process(amount=100)\n"
        "    assert gateway.charges == [100]\n"
    ),
    find=_find_no_real_assertion,
)


def _has_real_assertion(test: TestFunction) -> bool:
    """Whether anything in the test, nested code included, is a real assertion."""
    return any(
        _is_real_assertion(node)
        for statement in test.node.body
        for node in ast.walk(statement)
    )


def _takes_values_in(test: TestFunction) -> bool:
    """Whether the test is handed values: a fixture or parameter, or `self` it uses.

    A value handed in may be the outcome under test, made where the test can't see.
    """
    args = test.node.args
    names = [a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)]
    if any(name != "self" for name in names):
        return True
    return "self" in names and any(
        isinstance(node, ast.Name) and node.id == "self"
        for statement in test.node.body
        for node in ast.walk(statement)
    )


def _runs_anything(test: TestFunction) -> bool:
    """Whether the test calls or awaits anything but its assertions."""
    return any(
        isinstance(node, ast.Await)
        or (isinstance(node, ast.Call) and not _is_real_assertion(node))
        for statement in test.node.body
        for node in ast.walk(statement)
    )


def _find_no_action_under_test(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        if (
            not _has_real_assertion(test)
            or _takes_values_in(test)
            or _runs_anything(test)
        ):
            continue
        yield Hit(
            line=test.node.lineno,
            test=test.name,
            found=(
                f"`{test.name}` asserts but runs nothing: no call, no `await`, and "
                "no fixture or parameter to bring a value in."
            ),
            fix=(
                f"In `{test.name}`, call the code under test and assert on what it "
                "returns or changes; if the test only checks its own literals or "
                "Python itself, delete it."
            ),
        )


NO_ACTION_UNDER_TEST = Check(
    code="DS102",
    name="no-action-under-test",
    default_level=Level.FAIL,
    voice=(
        "You're asserting on numbers you wrote yourself, recruit! WHERE IS THE CODE?",
        "This test checks that Python works! Python doesn't need your help, maggot!",
        "No action, no test! Run the thing you claim to be testing!",
    ),
    why=(
        "A test that runs no code under test checks only its own literals or the "
        "language, so it passes whatever the code does."
    ),
    explain=(
        "Flags a test that has a real assertion but runs nothing: no call outside its "
        "assertions, no `await`, and no fixture or parameter (or `self` it uses) that "
        "could bring in the value under test. Such a test checks only values it wrote "
        "itself, or Python. Call the code under test and assert on its outcome."
    ),
    bad_example=(
        "def test_discount():\n    discount = 0.1\n    assert discount == 0.1\n"
    ),
    good_example=(
        "def test_discount_takes_ten_percent_off():\n"
        "    assert apply_discount(price=100, rate=0.1) == 90\n"
    ),
    find=_find_no_action_under_test,
)
