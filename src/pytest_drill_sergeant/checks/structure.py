"""The structure family (DS1xx): how a test is put together."""

import ast
from collections.abc import Iterable, Iterator

from pytest_drill_sergeant.checks.base import Check, Hit, TestFunction
from pytest_drill_sergeant.findings import Level

# Context managers that assert an exception or warning is raised.
_EXPECTING = frozenset({"raises", "warns", "deprecated_call"})


def _called_name(call: ast.Call) -> str | None:
    """The name a call is made through: `f` for `f()`, `g` for `a.b.g()`."""
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


def _is_real_assertion(node: ast.AST) -> bool:
    """Whether a node can fail the test on the outcome it checks.

    An `assert` of anything but a truthy constant counts, and so does a call to
    `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or `pytest.fail`, any
    `assert*`-named call (mock verification, unittest, helpers like
    `assert_frame_equal`) and raising `AssertionError`.
    """
    if isinstance(node, ast.Assert):
        return not (isinstance(node.test, ast.Constant) and bool(node.test.value))
    if isinstance(node, ast.Call):
        name = _called_name(node)
        return name is not None and (
            name.lower().startswith("assert") or name in _EXPECTING or name == "fail"
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


def _find_no_real_assertion(tests: Iterable[TestFunction]) -> Iterator[Hit]:
    for test in tests:
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
        "constant such as `assert True` can't), no `pytest.raises`, `pytest.warns` "
        "or `pytest.fail`, no `assert*` call such as a mock's `assert_called_once_with` "
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
