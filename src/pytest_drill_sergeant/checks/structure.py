"""The structure family (DS1xx): how a test is put together."""

import ast
from collections.abc import Iterator, Mapping
from enum import Enum

from pytest_drill_sergeant.checks.ast_tools import (
    calls_to,
    excinfo_names,
    is_known_non_act,
    is_real_assertion,
    module_imports,
    skips_unconditionally,
    value_params,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# pytest's helpers with a call form, by where the function to call sits: after the
# expected type, or first.
_CALL_FORM_AFTER_TYPE = frozenset({"pytest.raises", "pytest.warns"})
_DEPRECATED_CALL = frozenset({"pytest.deprecated_call"})


def _has_real_assertion(test: TestFunction) -> bool:
    """Whether anything in the test, nested code included, is a real assertion."""
    return any(is_real_assertion(node, test.imports) for node in walk_test(test))


def _last_call(test: TestFunction) -> ast.Call | None:
    """The call the test's last statement makes, if it makes one."""
    last = test.node.body[-1]
    value = last.value if isinstance(last, ast.Expr | ast.Assign) else None
    if isinstance(value, ast.Await):
        value = value.value
    return value if isinstance(value, ast.Call) else None


def _find_no_real_assertion(file: TestFile) -> Iterator[Hit]:
    names = module_imports(file.module)
    for test in file.tests:
        # A test that skips on every run is DS402's to report, not this check's.
        if _has_real_assertion(test) or skips_unconditionally(test, names):
            continue
        call = _last_call(test)
        target = (
            f"what `{ast.unparse(call.func)}(...)` returns or changes"
            if call is not None
            else "what the code under test returns or changes"
        )
        yield Hit.on(
            test,
            test.node.lineno,
            found=(
                "has no real assertion: no `assert` that can fail, no "
                "`pytest.raises`, no mock verification."
            ),
            fix=(
                f"assert on {target}, or wrap the call in "
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
        "the code didn't crash. Assert on what the code returns or changes. A test "
        "that skips on every run, by its own `pytest.mark.skip` or a `pytest.skip()` "
        "in its own body, is left to DS402 unconditional-skip."
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


def _takes_values_in(test: TestFunction) -> bool:
    """Whether the test is handed values: a fixture or parameter, or `self` it uses.

    A value handed in may be the outcome under test, made where the test can't see.
    """
    if value_params(test.node):
        return True
    return any(
        isinstance(node, ast.Name) and node.id == "self" for node in walk_test(test)
    )


def _calls_through_pytest(node: ast.AST, names: Mapping[str, str]) -> bool:
    """Whether a node is pytest's call form, which calls the function it is given.

    That is `pytest.raises(E, func, *args)`, `pytest.warns(W, func, *args)` or
    `pytest.deprecated_call(func, *args)`.
    """
    if not isinstance(node, ast.Call):
        return False
    if calls_to(node, _CALL_FORM_AFTER_TYPE, names):
        return len(node.args) > 1
    return calls_to(node, _DEPRECATED_CALL, names) and bool(node.args)


def _runs_anything(test: TestFunction) -> bool:
    """Whether the test calls or awaits anything but its assertions.

    pytest's call form (`pytest.raises(E, func, arg)`) runs `func`, so it counts.
    """
    return any(
        isinstance(node, ast.Await)
        or (isinstance(node, ast.Call) and not is_real_assertion(node, test.imports))
        or _calls_through_pytest(node, test.imports)
        for node in walk_test(test)
    )


def _find_no_action_under_test(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        if (
            not _has_real_assertion(test)
            or _takes_values_in(test)
            or _runs_anything(test)
        ):
            continue
        yield Hit.on(
            test,
            test.node.lineno,
            found=(
                "asserts but runs nothing: no call, no `await`, and no fixture or "
                "parameter to bring a value in."
            ),
            fix=(
                "call the code under test and assert on what it returns or "
                "changes; if the test only checks its own literals or Python "
                "itself, delete it."
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
        "assertions (pytest's call form, `pytest.raises(E, func, arg)`, counts as one), "
        "no `await`, and no fixture or parameter (or `self` it uses) that "
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


class _Step(Enum):
    """What a top-level statement of a test does, for the act and assert order."""

    ASSERT = "assert"
    ACT = "act"
    OTHER = "other"


_NESTED = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda


def _walk_own(node: ast.AST) -> Iterator[ast.AST]:
    """Every node under `node`, without descending into nested functions or classes."""
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, _NESTED):
            yield from _walk_own(child)


class _Order:
    """What reading a test's statements in order needs to know about the test."""

    def __init__(self, test: TestFunction) -> None:
        self.test = test
        self.names = test.imports
        self.excinfos = excinfo_names(test)

    def asserts(self, node: ast.AST) -> bool:
        """Whether a node asserts.

        That is a real assertion, or `.match` on a `pytest.raises`
        result, which checks the caught exception's message.
        """
        if is_real_assertion(node, self.names):
            return True
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "match"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.excinfos
        )

    def acts(self, node: ast.AST) -> bool:
        """Whether a statement is a call made for its effect: the act under test.

        That is a bare call or awaited call that isn't an assertion, known output
        or a pytest instrument (`ast_tools.is_known_non_act`). Cleanup is an act:
        after the last assertion it doesn't run when one fails. An assignment from
        a call is setup or reads a result, so it isn't one.
        """
        if not isinstance(node, ast.Expr):
            return False
        value = node.value.value if isinstance(node.value, ast.Await) else node.value
        return (
            isinstance(value, ast.Call)
            and not self.asserts(value)
            and not is_known_non_act(value, self.test)
        )

    def classify(self, statement: ast.stmt) -> _Step:
        """Whether a statement asserts, acts, or does neither.

        A statement that holds an assertion asserts, even if it also acts.
        """
        if isinstance(statement, _NESTED):
            return _Step.OTHER
        nodes = list(_walk_own(statement))
        if any(self.asserts(node) for node in nodes):
            return _Step.ASSERT
        if any(self.acts(node) for node in nodes):
            return _Step.ACT
        return _Step.OTHER

    def steps(self, body: list[ast.stmt]) -> list[tuple[ast.stmt, _Step]]:
        """Statements in order, each with what it does.

        A `with` block that isn't itself an assertion (a `mock.patch`, an open
        file) is opened up, so the statements inside it count in order.
        """
        steps: list[tuple[ast.stmt, _Step]] = []
        for statement in body:
            if isinstance(statement, ast.With | ast.AsyncWith) and not any(
                self.asserts(item.context_expr) for item in statement.items
            ):
                steps.extend(self.steps(statement.body))
            else:
                steps.append((statement, self.classify(statement)))
        return steps


def _steps(test: TestFunction) -> list[tuple[ast.stmt, _Step]]:
    """A test's statements in order, each with what it does."""
    return _Order(test).steps(test.node.body)


def _describe(statement: ast.stmt) -> str:
    """A short name for a statement: its call, or the kind of block it opens."""
    if isinstance(statement, ast.Expr):
        return f"`{ast.unparse(statement.value)}`"
    return f"the `{type(statement).__name__.lower()}` block"


def _find_assert_before_act(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        steps = _steps(test)
        last = max(
            (i for i, (_, step) in enumerate(steps) if step is _Step.ASSERT),
            default=None,
        )
        if last is None:
            continue
        unchecked = [s for s, step in steps[last + 1 :] if step is _Step.ACT]
        if not unchecked:
            continue
        act, last_assert = unchecked[0], steps[last][0]
        where = ", ".join(str(s.lineno) for s in unchecked)
        where = f"line {where}" if len(unchecked) == 1 else f"lines {where}"
        yield Hit.on(
            test,
            act.lineno,
            found=(
                f"runs {_describe(act)} on line {act.lineno} after its last "
                f"assertion (line {last_assert.lineno}), so nothing checks what it "
                "did."
            ),
            fix=(
                f"assert on what the act on {where} returns or changes, after it "
                "runs; keep an assertion before it only as a guard on the starting "
                "state. If it is cleanup, move it into a fixture (`tmp_path`, a "
                "`yield` fixture) or a `finally`."
            ),
        )


ASSERT_BEFORE_ACT = Check(
    code="DS103",
    name="assert-before-act",
    default_level=Level.FAIL,
    voice=(
        "You checked the ground, then fired blind! Assert AFTER you act, recruit!",
        "Asserting before the action is inspecting your rifle after the battle!",
        "The act runs and NOBODY looks at the result! Eyes on target, maggot!",
    ),
    why=(
        "When the act runs after the last assertion, the test checks only the "
        "starting state, so it stays green when the act does the wrong thing; and "
        "cleanup there never runs when an assertion fails."
    ),
    explain=(
        "Flags a test whose act runs after its last assertion: a bare call or "
        "`await` made for its effect, with no assertion following it. Not an act: "
        "output known from the code (the builtin `print()`, `logging` or a logger "
        "from `logging.getLogger()`); a method of a pytest built-in fixture the test "
        "takes (`caplog.clear()`, `capsys.readouterr()`, `monkeypatch.setenv()`); "
        "and `.match()` on what `pytest.raises` caught, which asserts. A name never "
        "counts: `logger.info()` or `server.stop()` on a value whose kind the file "
        "doesn't show is an act. Cleanup is flagged on purpose, even `os.remove()`: "
        "after the last assertion it never runs when one fails, so it belongs in a "
        "fixture (`tmp_path`, a `yield` fixture) or a `finally`. A guard assertion "
        "on the starting state is fine when the outcome is also asserted after the "
        "act. Move the assertion after the act, or add one there."
    ),
    bad_example=(
        "def test_add_item():\n"
        "    cart = Cart()\n"
        "    assert cart.items == []\n"
        "    cart.add('apple')\n"
    ),
    good_example=(
        "def test_add_item_puts_it_in_the_cart():\n"
        "    cart = Cart()\n"
        "    cart.add('apple')\n"
        "    assert cart.items == ['apple']\n"
    ),
    find=_find_assert_before_act,
)


def _checked_acts(steps: list[tuple[ast.stmt, _Step]]) -> list[ast.stmt]:
    """The first act of each run of acts that an assertion then checks.

    A run starts at an act with no act since the last assertion, and counts once
    an assertion follows it.
    """
    starts: list[ast.stmt] = []
    pending: ast.stmt | None = None
    for statement, step in steps:
        if step is _Step.ACT and pending is None:
            pending = statement
        elif step is _Step.ASSERT and pending is not None:
            starts.append(pending)
            pending = None
    return starts


def _find_interleaved_act_assert(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        acts = _checked_acts(_steps(test))
        if len(acts) < 2:  # noqa: PLR2004 -- two acts are what interleaving means
            continue
        second = acts[1]
        lines = ", ".join(str(act.lineno) for act in acts)
        yield Hit.on(
            test,
            second.lineno,
            found=(
                f"acts and asserts {len(acts)} times: after the assertions on the "
                f"act at line {acts[0].lineno}, {_describe(second)} on line "
                f"{second.lineno} acts again."
            ),
            fix=(
                f"split the test into one test per act (lines {lines}), each named "
                "for its behaviour, with any shared setup in a fixture."
            ),
        )


INTERLEAVED_ACT_ASSERT = Check(
    code="DS104",
    name="interleaved-act-assert",
    default_level=Level.WARN,
    voice=(
        "Act, assert, act, assert! That's not a test, it's a SCRIPT, recruit!",
        "One test, one mission! You're running three operations in one, maggot!",
        "When this goes red, which act failed? NOBODY KNOWS! Split it up!",
    ),
    why=(
        "A test that acts and asserts more than once checks several behaviours: "
        "when it fails, its name doesn't say which one broke, and a failing early "
        "step hides every later one."
    ),
    explain=(
        "Flags a test that acts, asserts, then acts and asserts again. An act is a "
        "bare call or `await` made for its effect, counted as DS103 counts it: "
        "known output such as `logging.info()`, or a method of a pytest built-in "
        "fixture the test takes such as `caplog.clear()`, is not one, and a name "
        "such as `reset_mock()` or `close()` never makes a call anything but an "
        "act. An assignment that reads "
        "a result between assertions isn't one, and a guard assertion before the "
        "only act is fine. Split the test into one test per act, with shared setup "
        "in a fixture. It warns by default rather than failing: a workflow or state "
        "test that steps through a sequence is sometimes rightly shaped this way, and "
        "a waiver records that it is."
    ),
    bad_example=(
        "def test_cart(cart):\n"
        "    cart.add('apple')\n"
        "    assert cart.items == ['apple']\n"
        "    cart.remove('apple')\n"
        "    assert cart.items == []\n"
    ),
    good_example=(
        "def test_add_puts_the_item_in_the_cart(cart):\n"
        "    cart.add('apple')\n"
        "    assert cart.items == ['apple']\n"
        "\n"
        "\n"
        "def test_remove_takes_the_item_out(cart_with_apple):\n"
        "    cart_with_apple.remove('apple')\n"
        "    assert cart_with_apple.items == []\n"
    ),
    find=_find_interleaved_act_assert,
)
