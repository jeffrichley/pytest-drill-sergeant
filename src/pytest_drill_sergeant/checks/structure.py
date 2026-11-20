"""The structure family (DS1xx): how a test is put together."""

import ast
import re
import sys
from collections import Counter
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
from pytest_drill_sergeant.checks.base import (
    Check,
    Comment,
    FunctionNode,
    Hit,
    TestFile,
    TestFunction,
    and_list,
)
from pytest_drill_sergeant.findings import Level

# pytest's helpers with a call form, by where the function to call sits: after the
# expected type, or first.
_CALL_FORM_AFTER_TYPE = frozenset({"pytest.raises", "pytest.warns"})
_DEPRECATED_CALL = frozenset({"pytest.deprecated_call"})
_PYTEST_FAIL = frozenset({"pytest.fail"})


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


def _find_long_test(file: TestFile) -> Iterator[Hit]:
    limit = file.thresholds.max_test_lines
    for test in file.tests:
        first, last = test.node.lineno, test.node.end_lineno or test.node.lineno
        length = last - first + 1
        if length <= limit:
            continue
        asserts = [
            node.lineno
            for node in walk_test(test)
            if isinstance(node, ast.stmt | ast.expr)
            and is_real_assertion(node, test.imports)
        ]
        body = test.node.body
        if ast.get_docstring(test.node) is not None and len(body) > 1:
            body = body[1:]
        setup = (
            f" Lines {body[0].lineno}-{min(asserts) - 1} run before its first "
            "assertion: what is setup there belongs in a fixture."
            if asserts and min(asserts) > body[0].lineno
            else ""
        )
        yield Hit.on(
            test,
            first,
            found=(
                f"is {length} lines long (lines {first}-{last}), more than the "
                f"{limit} a test may have."
            ),
            fix=(
                f"cut it to {limit} lines or fewer: split it into one test per "
                "behaviour it checks, each named for that behaviour, and move "
                f"shared setup into fixtures.{setup}"
            ),
        )


LONG_TEST = Check(
    code="DS105",
    name="long-test",
    default_level=Level.FAIL,
    voice=(
        "This test is longer than my last deployment! CUT IT DOWN, recruit!",
        "Nobody can read a test this long, maggot, and nobody will!",
        "One test, one mission! This is a whole CAMPAIGN!",
    ),
    why=(
        "A long test checks many things at once and buries what it is about: when "
        "it fails, finding the cause means reading all of it, and nobody reviews "
        "it closely."
    ),
    explain=(
        "Flags a test function longer than `drill_sergeant_max_test_lines` (50 by "
        "default), counted from its `def` line to its last line, blank lines, "
        "comments and docstring included. Its decorators don't count, so a long "
        "`parametrize` table is fine. Move setup into fixtures and split the test "
        "into one test per behaviour."
    ),
    bad_example=(
        "def test_checkout(shop):\n"
        + "".join(f"    shop.add_item('sku-{n}')\n" for n in range(50))
        + "    assert shop.checkout().total == 5000\n"
    ),
    good_example=(
        "def test_checkout_totals_the_cart(shop_with_fifty_items):\n"
        "    assert shop_with_fifty_items.checkout().total == 5000\n"
    ),
    find=_find_long_test,
)


def _test_file_for(name: str) -> str:
    """A test file named for a class or function.

    `TestLoanLimits` and `loan_limits` both give `test_loan_limits.py`.
    """
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+", name.removeprefix("Test"))
    return f"test_{'_'.join(w.lower() for w in words) or name.lower()}.py"


def _span(node: ast.ClassDef | FunctionNode) -> tuple[int, int]:
    """The lines a class or function takes, its decorators included."""
    first = min([node.lineno, *(d.lineno for d in node.decorator_list)])
    return first, node.end_lineno or node.lineno


def _imported_name(func: ast.expr, names: Mapping[str, str]) -> str | None:
    """The imported name a call goes through, as the test writes it.

    That is the name itself after `from m import f` (`Duration` for
    `Duration.total()`), or the module and its member after `import m`
    (`m.f` for `m.f.g()`). `None` when no import reaches the call.
    """
    chain: list[str] = []
    while isinstance(func, ast.Attribute):
        chain.insert(0, func.attr)
        func = func.value
    if not isinstance(func, ast.Name) or func.id not in names:
        return None
    if "." in names[func.id] or not chain:
        return func.id
    return f"{func.id}.{chain[0]}"


def _code_called(test: TestFunction) -> str | None:
    """The first imported code a test calls: what it exercises.

    Known from the file's imports, never from a name the test made up. pytest and
    the standard library are the test's tools, not the code under test.
    """
    for statement in test.node.body:
        for node in ast.walk(statement):
            if not isinstance(node, ast.Call):
                continue
            name = _imported_name(node.func, test.imports)
            if name is None:
                continue
            package = test.imports[name.split(".")[0]].split(".")[0]
            if package != "pytest" and package not in sys.stdlib_module_names:
                return name
    return None


def _module_level_plan(tests: list[TestFunction]) -> str:
    """How to split the module-level tests: grouped by the imported code they call."""
    spans = [_span(t.node) for t in tests]
    what = (
        f"its {_plural(len(tests), 'module-level test')} "
        f"(lines {min(a for a, _ in spans)}-{max(b for _, b in spans)})"
    )
    groups = Counter(_code_called(t) for t in tests)
    named = sorted(
        ((code, n) for code, n in groups.items() if code is not None),
        key=lambda item: (-item[1], item[0]),
    )
    if not named:
        return f"{what} into files of one behaviour each"
    moves = [
        f"the {n} that call `{code}` to `{_test_file_for(code.split('.')[-1])}`"
        if n > 1
        else f"the one that calls `{code}` to `{_test_file_for(code.split('.')[-1])}`"
        for code, n in named
    ]
    if None in groups:
        moves.append(f"the other {groups[None]} by the behaviour they check")
    return f"{what} by the code they call: {', '.join(moves)}"


def _split_plan(file: TestFile) -> str:
    """How to split a file: each test class to a file of its own, then the rest."""
    parts: list[str] = []
    for node in file.module.body:
        if not isinstance(node, ast.ClassDef):
            continue
        count = sum(t.name.startswith(f"{node.name}::") for t in file.tests)
        if count:
            first, last = _span(node)
            parts.append(
                f"`{node.name}` (lines {first}-{last}, {_plural(count, 'test')}) to "
                f"`{_test_file_for(node.name)}`"
            )
    loose = [t for t in file.tests if "::" not in t.name]
    if loose:
        parts.append(_module_level_plan(loose))
    return "; ".join(parts)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _find_long_file(file: TestFile) -> Iterator[Hit]:
    limit = file.thresholds.max_file_lines
    if file.lines <= limit or not file.tests:
        return
    yield Hit.on_file(
        file,
        found=(
            f"is {file.lines} lines long, more than the {limit} a test file may "
            f"have; it holds {_plural(len(file.tests), 'test')}."
        ),
        fix=(
            f"split it into files of at most {limit} lines: move "
            f"{_split_plan(file)}. Move fixtures the new files share into "
            "`conftest.py`."
        ),
    )


LONG_FILE = Check(
    code="DS106",
    name="long-file",
    default_level=Level.FAIL,
    voice=(
        "This file is a WAREHOUSE, recruit! Nobody can find anything in here!",
        "Five hundred lines and still growing? Split this barracks up, maggot!",
        "You've lost track of what's in this file, and so has everyone else!",
    ),
    why=(
        "A test file this long can't be held in mind: tests in it get duplicated or "
        "contradict each other because nobody, agent or person, can see what is "
        "already there."
    ),
    explain=(
        "Flags a test file longer than `drill_sergeant_max_file_lines` (500 by "
        "default), counting every line, once per file, on line 1. A file with no "
        "tests in it isn't flagged. The fix says how to split it: each test class "
        "to a file of its own, named for the class, and the module-level tests into "
        "files grouped by the behaviour they cover, with shared fixtures in "
        "`conftest.py`."
    ),
    bad_example=(
        "class TestLoans:\n"
        + "".join(
            f"    def test_loan_{n}(self, library):\n"
            f"        assert library.lend({n}).days == {n}\n\n"
            for n in range(100)
        )
        + "\n\nclass TestFines:\n"
        + "".join(
            f"    def test_fine_{n}(self, library):\n"
            f"        assert library.fine(days={n}) == {n * 25}\n\n"
            for n in range(100)
        )
    ),
    good_example=(
        "# test_loans.py holds TestLoans, test_fines.py holds TestFines.\n"
        "class TestLoans:\n"
        "    def test_loan_lasts_21_days(self, library):\n"
        "        assert library.lend('978-0-13-468599-1').days == 21\n"
    ),
    find=_find_long_file,
)


_CONDITIONAL = ast.If | ast.Match | ast.For | ast.AsyncFor | ast.While
_LOOP = ast.For | ast.AsyncFor | ast.While
_LITERAL_COLLECTION = ast.List | ast.Tuple | ast.Set

# How long a literal may be and still be quoted whole in a fix.
_QUOTE_LIMIT = 60


def _fails_outright(statement: ast.stmt, test: TestFunction) -> bool:
    """Whether a statement only fails the test.

    That is `pytest.fail(...)`, `raise AssertionError` or `assert False`.
    """
    if isinstance(statement, ast.Expr):
        return calls_to(statement.value, _PYTEST_FAIL, test.imports)
    if isinstance(statement, ast.Assert):
        return isinstance(statement.test, ast.Constant) and not statement.test.value
    return isinstance(statement, ast.Raise) and is_real_assertion(
        statement, test.imports
    )


def _is_a_hand_written_assert(statement: ast.stmt, test: TestFunction) -> bool:
    """Whether a statement is an `if` that is itself the assertion.

    That is an `if` with no `else` that only fails the test (`if total != 3:
    pytest.fail(...)`): it checks one outcome on every path, as `assert` does.
    """
    return (
        isinstance(statement, ast.If)
        and not statement.orelse
        and all(_fails_outright(s, test) for s in statement.body)
    )


def _asserting_conditionals(
    body: list[ast.stmt], test: TestFunction
) -> Iterator[ast.stmt]:
    """The outermost branches and loops in a body that hold a real assertion.

    Nested code (a helper `def` in the test) is searched too, as part of the test.
    """
    for statement in body:
        if (
            isinstance(statement, _CONDITIONAL)
            and not _is_a_hand_written_assert(statement, test)
            and any(
                is_real_assertion(node, test.imports) for node in ast.walk(statement)
            )
        ):
            yield statement
            continue
        for child in ast.iter_child_nodes(statement):
            if isinstance(child, ast.stmt):
                yield from _asserting_conditionals([child], test)
            elif isinstance(child, ast.ExceptHandler | ast.match_case):
                yield from _asserting_conditionals(child.body, test)


def _module_literals(module: ast.Module) -> dict[str, ast.expr]:
    """The top-level names bound once, to a literal list, tuple or set."""
    bound: dict[str, list[ast.expr | None]] = {}
    for statement in module.body:
        value: ast.expr | None
        if isinstance(statement, ast.Assign):
            targets, value = statement.targets, statement.value
        elif isinstance(statement, ast.AnnAssign):
            targets, value = [statement.target], statement.value
        else:
            continue
        for target in targets:
            for node in ast.walk(target):
                if isinstance(node, ast.Name):
                    bound.setdefault(node.id, []).append(value)
    return {
        name: values[0]
        for name, values in bound.items()
        if len(values) == 1 and isinstance(values[0], _LITERAL_COLLECTION)
    }


def _binds_in_test(name: str, test: TestFunction) -> bool:
    """Whether the test takes or assigns a name itself."""
    return name in value_params(test.node) or any(
        isinstance(node, ast.Name)
        and node.id == name
        and isinstance(node.ctx, ast.Store)
        for node in walk_test(test)
    )


def _parametrize_values(
    loop: ast.For | ast.AsyncFor, file: TestFile, test: TestFunction
) -> tuple[str, str] | None:
    """The values a loop runs over, when the file writes them out.

    That is a literal in place, or a top-level name bound once to one. Returned as
    `parametrize` would take them, with where they are when they are too long to
    quote (`[...]`, the values from line 12). A set becomes a list, which keeps its
    order.
    """
    values = loop.iter
    if isinstance(values, _LITERAL_COLLECTION):
        text = ast.unparse(ast.List(elts=values.elts, ctx=ast.Load()))
        if len(text) <= _QUOTE_LIMIT:
            return text, ""
        count = _plural(len(values.elts), "value")
        return "[...]", f" with the {count} from line {values.lineno}"
    if (
        isinstance(values, ast.Name)
        and values.id in _module_literals(file.module)
        and not _binds_in_test(values.id, test)
    ):
        return values.id, ""
    return None


def _conditional_fix(
    statement: ast.stmt, file: TestFile, test: TestFunction
) -> tuple[str, str]:
    """What a branch or loop with an assertion in it is, and how to fix it."""
    kind = type(statement).__name__.lower().replace("asyncfor", "async for")
    if not isinstance(statement, _LOOP):
        article = "an" if kind == "if" else "a"
        return (
            f"has {article} `{kind}` on line {statement.lineno} with assertions "
            "inside it, so they run only on some paths, and the test passes on the "
            "others.",
            "set up the case so its outcome is known, and assert that one outcome "
            "with no branch; write one test per path.",
        )
    found = (
        f"asserts inside a `{kind}` loop on line {statement.lineno}: if the loop "
        "runs zero times, nothing is checked and the test still passes."
    )
    if isinstance(statement, ast.For | ast.AsyncFor):
        values = _parametrize_values(statement, file, test)
        if values is not None:
            names = ast.unparse(statement.target)
            if isinstance(statement.target, ast.Tuple):
                names = names.strip("()")
            args, where = values
            return found, (
                "replace the loop with "
                f'`@pytest.mark.parametrize("{names}", {args})`{where}, so each '
                "case runs, passes and fails as its own test."
            )
        source = ast.unparse(statement.iter)
        if len(source) <= _QUOTE_LIMIT:
            target = ast.unparse(statement.target)
            return found, (
                f"assert once on everything `{source}` gives, as a whole (`assert "
                f"[... {kind} {target} in {source}] == [...]`), so an empty result "
                "fails the test; or `parametrize` over known inputs."
            )
    return found, (
        "assert once, after the loop, on the whole outcome, so a loop that runs "
        "zero times fails the test; or `parametrize` over known inputs."
    )


def _find_conditional_logic(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for statement in _asserting_conditionals(test.node.body, test):
            found, fix = _conditional_fix(statement, file, test)
            yield Hit.on(test, statement.lineno, found=found, fix=fix)


CONDITIONAL_LOGIC = Check(
    code="DS107",
    name="conditional-logic",
    default_level=Level.WARN,
    voice=(
        "IF? There is no IF in a test, recruit! You know the outcome or you don't!",
        "A test that takes whichever path is open passes on every path, maggot!",
        "Your loop checks nothing when it's empty, and you'll never know it!",
    ),
    why=(
        "An assertion under a branch or in a loop runs only on some paths: the test "
        "passes on the others, or when the loop runs zero times, without checking "
        "anything."
    ),
    explain=(
        "Flags an `if`, `match`, `for` or `while` in a test with a real assertion "
        "inside it, once for the outermost one. An `if` with no assertion inside it, "
        "such as one that calls `pytest.skip`, a loop that only builds data, and a "
        "conditional expression or comprehension are left alone, and so is a `try`, "
        "which swallowed-exception reads. Branching: set up the case so the outcome "
        "is known, assert it unconditionally, and write one test per path. A loop "
        "over values the file writes out (a list, tuple or set literal, or a "
        "top-level name bound to one) gets a `parametrize` suggestion naming them. "
        "Any other loop: assert on the whole collection at once, which fails when "
        "it's empty. It warns by default rather than failing: asserting on each item "
        "of a collection the code returns is sometimes the clearest test, and a "
        "waiver records that it is."
    ),
    bad_example=(
        "def test_parse_quantity():\n"
        '    for raw, expected in [("1", 1), ("1k", 1000)]:\n'
        "        assert parse_quantity(raw) == expected\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        '@pytest.mark.parametrize(("raw", "expected"), [("1", 1), ("1k", 1000)])\n'
        "def test_parse_quantity(raw, expected):\n"
        "    assert parse_quantity(raw) == expected\n"
    ),
    find=_find_conditional_logic,
)


class _Section(Enum):
    """A section an AAA comment heads, by the name the comment gives it."""

    ARRANGE = "Arrange"
    ACT = "Act"
    ASSERT = "Assert"
    ACT_AND_ASSERT = "Act and assert"


# Where each section stands in a test, first to last, as (first, last): `Act and
# assert` stands for both of its sections.
_SECTION_SPAN = {
    _Section.ARRANGE: (0, 0),
    _Section.ACT: (1, 1),
    _Section.ASSERT: (2, 2),
    _Section.ACT_AND_ASSERT: (1, 2),
}

# An AAA comment: the section's name alone, or followed by `:` or a dash and any
# text, in any case. `# Assert the total` is prose, not an AAA comment.
_AAA_COMMENT = re.compile(
    r"#\s*(?P<name>act(?P<both>\s+and\s+assert|\s*&\s*assert)?|arrange|assert)"
    r"\s*(?:[:\-\u2013\u2014].*)?",
    re.IGNORECASE | re.DOTALL,
)


def _section_of(comment: Comment) -> _Section | None:
    """The section a comment alone on its line heads, if it is an AAA comment."""
    match = _AAA_COMMENT.fullmatch(comment.text.strip())
    if match is None:
        return None
    if match["both"]:
        return _Section.ACT_AND_ASSERT
    return _Section(match["name"].capitalize())


def _labels(file: TestFile, test: TestFunction) -> list[tuple[int, _Section]]:
    """The AAA comments inside a test, each with the section it heads, in order."""
    first, last = test.node.lineno, test.node.end_lineno or test.node.lineno
    return [
        (comment.line, section)
        for comment in file.comments
        if first < comment.line <= last
        and (section := _section_of(comment)) is not None
    ]


def _runs(order: _Order, statement: ast.stmt) -> bool:
    """Whether a statement runs anything: what an `# Act` section must hold.

    That is a call or `await` that isn't an assertion, known output or a pytest
    instrument (`ast_tools.is_known_non_act`). Unlike DS103's act, an assignment from a call counts: `total = cart.total()`
    runs the code under test as surely as `cart.add(item)` does.
    """
    return any(
        isinstance(node, ast.Await)
        or (
            isinstance(node, ast.Call)
            and not order.asserts(node)
            and not is_known_non_act(node, order.test)
        )
        for node in _walk_own(statement)
    )


def _own_steps(order: _Order) -> list[tuple[ast.stmt, _Step]]:
    """A test's statements in order, each with what it does, its docstring aside."""
    body = order.test.node.body
    if ast.get_docstring(order.test.node) is not None:
        body = body[1:]
    return order.steps(body)


def _plan(order: _Order, steps: list[tuple[ast.stmt, _Step]]) -> dict[_Section, int]:
    """Where each AAA comment belongs, by the line of the statement it heads.

    Assert heads the first assertion after the last act; Act, the last statement
    before that one that runs anything, or, with none, the assertion itself as `Act
    and assert`; Arrange, the first statement, when anything comes before the act.
    Empty when no assertion follows the last act (DS103's to report).
    """
    acts = [i for i, (_, step) in enumerate(steps) if step is _Step.ACT]
    after = acts[-1] if acts else -1
    assert_at = next(
        (i for i, (_, s) in enumerate(steps) if i > after and s is _Step.ASSERT),
        None,
    )
    if assert_at is None:
        return {}
    act_at = max(
        (i for i in range(assert_at) if _runs(order, steps[i][0])), default=None
    )
    plan: dict[_Section, int] = {}
    if (assert_at if act_at is None else act_at) > 0:
        plan[_Section.ARRANGE] = steps[0][0].lineno
    if act_at is None:
        plan[_Section.ACT_AND_ASSERT] = steps[assert_at][0].lineno
    else:
        plan[_Section.ACT] = steps[act_at][0].lineno
        plan[_Section.ASSERT] = steps[assert_at][0].lineno
    return plan


def _comment(section: _Section) -> str:
    return f"`# {section.value}`"


def _placement(section: _Section, plan: Mapping[_Section, int]) -> str:
    return f"{_comment(section)} above line {plan[section]}"


def _missing_fix(
    missing: list[_Section],
    labels: list[tuple[int, _Section]],
    plan: Mapping[_Section, int],
) -> str:
    """How to add the AAA comments a test lacks, where its structure puts them."""
    if not plan:
        return (
            "assert on what the test's last act did, after it, then head its "
            "sections with `# Arrange`, `# Act` and `# Assert`."
        )
    steps: list[str] = []
    if _Section.ACT_AND_ASSERT in plan and {_Section.ACT, _Section.ASSERT} & set(
        missing
    ):
        missing = [s for s in missing if s not in {_Section.ACT, _Section.ASSERT}]
        held = [(line, s) for line, s in labels if s in {_Section.ACT, _Section.ASSERT}]
        if held:
            line, section = held[0]
            steps.append(
                f"make {_comment(section)} on line {line} `# Act and assert`, as "
                "the act is inside the assertion"
            )
        else:
            missing.append(_Section.ACT_AND_ASSERT)
    if missing:
        steps.insert(0, f"add {and_list([_placement(s, plan) for s in missing])}")
    return f"{'; '.join(steps)}."


def _find_missing(
    test: TestFunction,
    labels: list[tuple[int, _Section]],
    steps: list[tuple[ast.stmt, _Step]],
    plan: Mapping[_Section, int],
) -> Iterator[Hit]:
    """A hit naming the AAA comments a test lacks, if it lacks any.

    Arrange is lacking when statements come before the first AAA comment and it
    isn't `# Arrange` (or, with none, when the plan has setup); Act and Assert
    always, unless `# Act and assert` heads both.
    """
    present = {section for _, section in labels}
    missing: list[_Section] = []
    if labels:
        if steps[0][0].lineno < labels[0][0] and labels[0][1] is not _Section.ARRANGE:
            missing.append(_Section.ARRANGE)
    elif _Section.ARRANGE in plan:
        missing.append(_Section.ARRANGE)
    if not present & {_Section.ACT, _Section.ACT_AND_ASSERT}:
        missing.append(_Section.ACT)
    if not present & {_Section.ASSERT, _Section.ACT_AND_ASSERT}:
        missing.append(_Section.ASSERT)
    if not missing:
        return
    if not labels:
        found = "has no Arrange/Act/Assert comments."
    else:
        names = and_list([_comment(s) for s in missing])
        found = f"lacks its {names} comment{'s' if len(missing) > 1 else ''}."
    if _Section.ARRANGE in missing:
        plan = {**plan, _Section.ARRANGE: steps[0][0].lineno}
    yield Hit.on(
        test, test.node.lineno, found=found, fix=_missing_fix(missing, labels, plan)
    )


def _under(
    test: TestFunction,
    labels: list[tuple[int, _Section]],
    steps: list[tuple[ast.stmt, _Step]],
) -> list[list[tuple[ast.stmt, _Step]] | None]:
    """The statements each AAA comment heads: those after it, up to the next one.

    `None` for a comment that heads no statement at all; a `with` line it heads
    counts, though the statements inside are read one by one.
    """
    bounds = [line for line, _ in labels[1:]] + [sys.maxsize]
    starts = [n.lineno for n in walk_test(test) if isinstance(n, ast.stmt)]
    return [
        [(s, step) for s, step in steps if line < s.lineno < bound]
        if any(line < start < bound for start in starts)
        else None
        for (line, _), bound in zip(labels, bounds, strict=False)
    ]


def _contradiction(
    order: _Order,
    label: tuple[int, _Section],
    held: list[tuple[ast.stmt, _Step]] | None,
    plan: Mapping[_Section, int],
    present: set[_Section],
) -> tuple[str, str] | None:
    """What an AAA comment says that the statements under it contradict, if anything.

    Arrange may hold anything, a guard assertion included; Act must run something
    and assert nothing; Assert must assert and not act; Act and assert must assert.
    An assertion under `# Act` with no `# Assert` in the test, or an act under
    `# Assert` with no `# Act`, is the missing comment's to report.
    """
    line, section = label
    comment = _comment(section)
    if held is None:
        return (
            f"has {comment} on line {line} heading no statements.",
            "remove it, or move it above the statements it names.",
        )
    asserts = [s for s, step in held if step is _Step.ASSERT]
    acts = [s for s, step in held if step is _Step.ACT]
    if section is _Section.ACT and asserts and _Section.ASSERT in present:
        return (
            f"asserts on line {asserts[0].lineno}, under {comment} on line {line}.",
            f"move the assertion under `# Assert`; if the act is inside it "
            f"(`pytest.raises`, `assert f() == ...`), make the comment on line "
            f"{line} `# Act and assert`.",
        )
    if section is _Section.ACT and not any(_runs(order, s) for s, _ in held):
        if _Section.ACT in plan:
            fix = (
                f"move `# Act` above line {plan[_Section.ACT]}, the last call "
                "before the assertions."
            )
        elif _Section.ACT_AND_ASSERT in plan:
            fix = (
                f"the act is inside the assertion on line "
                f"{plan[_Section.ACT_AND_ASSERT]}: remove `# Act` and head the "
                "assertion with `# Act and assert`."
            )
        else:
            fix = "move `# Act` above the call to the code under test."
        return (
            f"runs nothing under {comment} on line {line}: no call, no `await`.",
            fix,
        )
    if section is _Section.ASSERT and acts and _Section.ACT in present:
        return (
            f"runs {_describe(acts[0])} on line {acts[0].lineno}, under {comment} "
            f"on line {line}.",
            f"move it above line {line}, under `# Act`, and assert on what it did.",
        )
    if section in {_Section.ASSERT, _Section.ACT_AND_ASSERT} and not asserts:
        return (
            f"asserts nothing under {comment} on line {line}.",
            f"move {comment} above the assertions, or assert on what the act did.",
        )
    return None


def _find_contradictions(
    order: _Order,
    labels: list[tuple[int, _Section]],
    steps: list[tuple[ast.stmt, _Step]],
    plan: Mapping[_Section, int],
) -> Iterator[Hit]:
    """A hit for each AAA comment that the test's structure contradicts."""
    test = order.test
    present = {section for _, section in labels}
    if (
        labels
        and labels[0][1] is _Section.ARRANGE
        and steps[0][0].lineno < labels[0][0]
    ):
        yield Hit.on(
            test,
            labels[0][0],
            found=(
                f"has `# Arrange` on line {labels[0][0]}, after the code on line "
                f"{steps[0][0].lineno}."
            ),
            fix=f"move `# Arrange` above line {steps[0][0].lineno}.",
        )
    reached: tuple[int, _Section] | None = None
    for (line, section), held in zip(labels, _under(test, labels, steps), strict=True):
        if (
            reached is not None
            and _SECTION_SPAN[section][0] <= _SECTION_SPAN[reached[1]][1]
        ):
            yield Hit.on(
                test,
                line,
                found=(
                    f"has {_comment(section)} on line {line} after "
                    f"{_comment(reached[1])} on line {reached[0]}: the sections "
                    "are out of order."
                ),
                fix=(
                    "keep one each of `# Arrange`, `# Act` and `# Assert`, in that "
                    "order; a test that acts again after asserting checks two "
                    "behaviours: split it."
                ),
            )
            continue
        reached = (line, section)
        problem = _contradiction(order, (line, section), held, plan, present)
        if problem is not None:
            found, fix = problem
            yield Hit.on(test, line, found=found, fix=fix)


def _find_aaa_comments(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        order = _Order(test)
        steps = _own_steps(order)
        # A test with no assertion is DS101's to report, not this check's.
        if not any(step is _Step.ASSERT for _, step in steps):
            continue
        labels = _labels(file, test)
        plan = _plan(order, steps)
        yield from _find_missing(test, labels, steps, plan)
        yield from _find_contradictions(order, labels, steps, plan)


AAA_COMMENTS = Check(
    code="DS108",
    name="aaa-comments",
    default_level=Level.OFF,
    voice=(
        "Arrange! Act! Assert! Sound off by the numbers, recruit!",
        "Your comment says ASSERT and your code says otherwise! Who's lying, maggot?",
        "No section markers? This test is a march with no cadence!",
    ),
    why=(
        "Arrange/Act/Assert comments let a reader find a test's setup, its act and "
        "its checks at a glance; a comment that doesn't match the code misleads "
        "worse than none."
    ),
    explain=(
        "Off by default; turn it on with `drill_sergeant_levels` (`DS108=fail`). "
        "Flags a test with an assertion that lacks its Arrange/Act/Assert comments, "
        "or has one the code contradicts. An AAA comment stands alone on its line "
        "and is `# Arrange`, `# Act`, `# Assert` or `# Act and assert` (also `# Act "
        "& assert`), in any case, alone or followed by `:` or a dash and any text "
        "(`# Arrange - a cart with one item`); `# Assert the total` is prose. "
        "Comments are read with `tokenize`, so text in a string never counts. Each "
        "heads the statements below it, up to the next. `# Act` and `# Assert` are "
        "required, or `# Act and assert` for both, as when the act is inside the "
        "assertion (`pytest.raises`, `assert total(cart) == 3`). `# Arrange` is "
        "required only when statements come before the act; it may hold anything, a "
        "guard assertion included. Contradictions: `# Act` that runs nothing (no "
        "call or `await`; an assignment from a call counts) or that asserts, "
        "`# Assert` that asserts nothing or runs an act (a bare call, as DS103 counts "
        "it), a comment heading no statements, and sections out of order or "
        "repeated. A test with no assertion is left to DS101."
    ),
    bad_example=(
        "def test_add_item(cart):\n"
        "    # Arrange\n"
        "    item = 'apple'\n"
        "    # Assert\n"
        "    cart.add(item)\n"
        "    assert cart.items == [item]\n"
    ),
    good_example=(
        "def test_add_item(cart):\n"
        "    # Arrange\n"
        "    item = 'apple'\n"
        "    # Act\n"
        "    cart.add(item)\n"
        "    # Assert\n"
        "    assert cart.items == [item]\n"
    ),
    find=_find_aaa_comments,
)
