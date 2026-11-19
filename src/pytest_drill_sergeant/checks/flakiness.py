"""The flakiness family (DS8xx): tests whose outcome rides on time or chance."""

import ast
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# The event-loop sleeps, which yield without waiting when given a zero delay.
_ASYNC_SLEEPS = frozenset({"asyncio.sleep", "trio.sleep", "anyio.sleep"})

# The calls that read the wall clock.
_CLOCK_READS = frozenset(
    {
        "time.time",
        "time.time_ns",
        "datetime.datetime.now",
        "datetime.datetime.utcnow",
        "datetime.datetime.today",
        "datetime.date.today",
    }
)

# What freezes the clock: as a decorator or `with`, and as a fixture a test takes.
_FREEZERS = frozenset(
    {"freezegun.freeze_time", "time_machine.travel", "pytest.mark.freeze_time"}
)
_FREEZER_FIXTURES = frozenset({"freezer", "time_machine"})

# The draws from a global generator, by the module whose seed governs them.
_DRAWS = {
    "random": frozenset(
        {
            "betavariate",
            "binomialvariate",
            "choice",
            "choices",
            "expovariate",
            "gammavariate",
            "gauss",
            "getrandbits",
            "lognormvariate",
            "normalvariate",
            "paretovariate",
            "randbytes",
            "randint",
            "random",
            "randrange",
            "sample",
            "shuffle",
            "triangular",
            "uniform",
            "vonmisesvariate",
            "weibullvariate",
        }
    ),
    "numpy.random": frozenset(
        {
            "beta",
            "binomial",
            "choice",
            "exponential",
            "gamma",
            "normal",
            "permutation",
            "poisson",
            "rand",
            "randint",
            "randn",
            "random",
            "random_sample",
            "shuffle",
            "standard_normal",
            "uniform",
        }
    ),
}

# The constructors that seed a generator from entropy when given no seed.
_GENERATORS = frozenset(
    {"random.Random", "numpy.random.default_rng", "numpy.random.RandomState"}
)


def _bind_imports(
    statement: ast.Import | ast.ImportFrom, names: dict[str, str]
) -> None:
    """Record the local names an import binds, each with what it stands for."""
    if isinstance(statement, ast.Import):
        for alias in statement.names:
            if alias.asname:
                names[alias.asname] = alias.name
            else:
                top = alias.name.split(".")[0]
                names[top] = top
    elif statement.module and not statement.level:
        for alias in statement.names:
            names[alias.asname or alias.name] = f"{statement.module}.{alias.name}"


def _module_names(module: ast.Module) -> dict[str, str]:
    """The names a module binds by import at its top level, minus any it rebinds.

    Imports under a top-level `if` or `try` count, and a fallback there (`np = None`
    after `except ImportError`) doesn't undo them; a later top-level `def`, `class`
    or assignment of the same name wins, as it does at run time.
    """
    names: dict[str, str] = {}
    for statement in module.body:
        if isinstance(statement, ast.If | ast.Try):
            for node in ast.walk(statement):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    _bind_imports(node, names)
        elif isinstance(statement, ast.Import | ast.ImportFrom):
            _bind_imports(statement, names)
        else:
            for bound in _bound_names(statement):
                names.pop(bound, None)
    return names


def _bound_names(statement: ast.stmt) -> Iterator[str]:
    """The names a function, class or assignment statement binds where it stands."""
    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        yield statement.name
        return
    targets = statement.targets if isinstance(statement, ast.Assign) else []
    for target in targets:
        for node in ast.walk(target):
            if isinstance(node, ast.Name):
                yield node.id


def _test_names(test: TestFunction, module_names: Mapping[str, str]) -> dict[str, str]:
    """The imported names a test sees: the module's, its own imports, minus shadows.

    A parameter (a fixture) or a name the test binds itself, such as a nested
    `def sleep`, hides the module's import of the same name.
    """
    names = dict(module_names)
    shadows = {arg.arg for arg in ast.walk(test.node.args) if isinstance(arg, ast.arg)}
    for node in ast.walk(test.node):
        if node is test.node:
            continue
        if isinstance(node, ast.Import | ast.ImportFrom):
            _bind_imports(node, names)
        elif isinstance(node, ast.stmt):
            shadows.update(_bound_names(node))
    for shadow in shadows:
        names.pop(shadow, None)
    return names


def _qualified(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """What an expression names through the imports in scope, or None.

    `t.sleep` is `time.sleep` after `import time as t`; a name no import reaches is
    None.
    """
    if isinstance(expr, ast.Name):
        return names.get(expr.id)
    if isinstance(expr, ast.Attribute):
        base = _qualified(expr.value, names)
        return f"{base}.{expr.attr}" if base else None
    return None


@dataclass(frozen=True)
class _Call:
    """A call in a test whose target an import reaches.

    Attributes:
        test: The test it is in.
        node: The call.
        target: What it calls, in full (`time.sleep`).
        frozen: Whether it runs under a frozen clock.
    """

    test: TestFunction
    node: ast.Call
    target: str
    frozen: bool


def _calls(file: TestFile) -> Iterator[_Call]:
    """Every call in every test whose target an import reaches, in source order."""
    module_names = _module_names(file.module)
    for test in file.tests:
        names = _test_names(test, module_names)
        calls = [node for node in ast.walk(test.node) if isinstance(node, ast.Call)]
        frozen = _frozen_calls(file, test, names)
        for call in sorted(calls, key=lambda c: (c.lineno, c.col_offset)):
            target = _qualified(call.func, names)
            if target:
                yield _Call(test, call, target, frozen=call in frozen)


def _freezes(expr: ast.expr, names: Mapping[str, str]) -> bool:
    """Whether a decorator or `with` item freezes the clock."""
    target = expr.func if isinstance(expr, ast.Call) else expr
    return _qualified(target, names) in _FREEZERS


def _frozen_calls(
    file: TestFile, test: TestFunction, names: Mapping[str, str]
) -> set[ast.Call]:
    """The calls in a test that run under a frozen clock.

    All of them when the test or a class around it is decorated with a freezer or
    the test takes a freezer fixture; otherwise those inside a freezer's `with`.
    """
    classes = [
        node
        for node in ast.walk(file.module)
        if isinstance(node, ast.ClassDef) and test.node in node.body
    ]
    decorators = [d for owner in [test.node, *classes] for d in owner.decorator_list]
    params = {arg.arg for arg in ast.walk(test.node.args) if isinstance(arg, ast.arg)}
    scopes: list[ast.AST] = []
    if any(_freezes(d, names) for d in decorators) or params & _FREEZER_FIXTURES:
        scopes.append(test.node)
    scopes.extend(
        node
        for node in ast.walk(test.node)
        if isinstance(node, ast.With | ast.AsyncWith)
        and any(_freezes(item.context_expr, names) for item in node.items)
    )
    return {
        node
        for scope in scopes
        for node in ast.walk(scope)
        if isinstance(node, ast.Call)
    }


def _is_zero(call: ast.Call) -> bool:
    """Whether a call's first argument is the literal zero."""
    return (
        bool(call.args)
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == 0
    )


def _find_sleep_in_test(file: TestFile) -> Iterator[Hit]:
    # A frozen clock doesn't stop a sleep: freezegun and time-machine leave it real.
    for call in _calls(file):
        if call.target != "time.sleep" and (
            call.target not in _ASYNC_SLEEPS or _is_zero(call.node)
        ):
            continue
        test, line, written = call.test.name, call.node.lineno, ast.unparse(call.node)
        yield Hit(
            line=line,
            test=test,
            found=f"`{test}` sleeps for real time: `{written}`.",
            fix=(
                f"In `{test}`, replace `{written}` on line {line} with a fake or "
                "frozen clock, or wait on the condition itself (an event, a join, a "
                "poll with a timeout)."
            ),
        )


def _find_wall_clock_read(file: TestFile) -> Iterator[Hit]:
    for call in _calls(file):
        if call.target not in _CLOCK_READS or call.frozen:
            continue
        test, line, written = call.test.name, call.node.lineno, ast.unparse(call.node)
        yield Hit(
            line=line,
            test=test,
            found=f"`{test}` reads the wall clock: `{written}`.",
            fix=(
                f"In `{test}`, replace `{written}` on line {line} with a fixed time "
                "or an injected clock, or freeze the clock with "
                "`freezegun.freeze_time` or `time_machine.travel`."
            ),
        )


def _seeded(nodes: list[ast.AST], names: Mapping[str, str]) -> set[str]:
    """The global generators (`random`, `numpy.random`) the nodes seed with a value.

    `random.seed()` with nothing to seed from reseeds from entropy, so it doesn't
    count.
    """
    seeded: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if not isinstance(node, ast.Call) or not (node.args or node.keywords):
                continue
            target = _qualified(node.func, names) or ""
            family, _, attr = target.rpartition(".")
            if attr == "seed" and family in _DRAWS:
                seeded.add(family)
    return seeded


def _is_autouse_fixture(node: ast.stmt, names: Mapping[str, str]) -> bool:
    """Whether a statement defines a fixture pytest runs before every test."""
    return isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and any(
        isinstance(d, ast.Call)
        and _qualified(d.func, names) == "pytest.fixture"
        and any(
            k.arg == "autouse"
            and isinstance(k.value, ast.Constant)
            and k.value.value is True
            for k in d.keywords
        )
        for d in node.decorator_list
    )


def _find_unseeded_random(file: TestFile) -> Iterator[Hit]:
    names = _module_names(file.module)
    file_wide: list[ast.AST] = [
        node
        for node in file.module.body
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        or _is_autouse_fixture(node, names)
    ]
    seeded_by_file = _seeded(file_wide, names)
    seeded_by_test: dict[str, set[str]] = {}
    for call in _calls(file):
        test = call.test.name
        if test not in seeded_by_test:
            seeded_by_test[test] = seeded_by_file | _seeded([call.test.node], names)
        family, _, attr = call.target.rpartition(".")
        unseeded_draw = (
            attr in _DRAWS.get(family, ()) and family not in seeded_by_test[test]
        )
        unseeded_generator = call.target in _GENERATORS and not (
            call.node.args or call.node.keywords
        )
        if not (unseeded_draw or unseeded_generator):
            continue
        line, written = call.node.lineno, ast.unparse(call.node)
        yield Hit(
            line=line,
            test=test,
            found=f"`{test}` draws unseeded random values: `{written}`.",
            fix=(
                f"In `{test}`, replace `{written}` on line {line} with fixed values "
                "or a seeded generator (`random.Random(1234)`, "
                "`numpy.random.default_rng(1234)`)."
            ),
        )


SLEEP_IN_TEST = Check(
    code="DS801",
    name="sleep-in-test",
    default_level=Level.FAIL,
    voice=(
        "Napping on duty, recruit? Tests don't SLEEP on my watch!",
        "You picked that number out of thin air! On a slow CI box it's too short, "
        "everywhere else it's wasted!",
        "Waiting and hoping is not a strategy, maggot! Wait for the EVENT!",
    ),
    why=(
        "A sleep guesses how long something takes: too short on a loaded machine and "
        "the test fails at random, too long and every run pays for it."
    ),
    explain=(
        "Flags a test that calls `time.sleep`, or awaits `asyncio.sleep`, "
        "`trio.sleep` or `anyio.sleep` with a delay other than a literal zero "
        "(`asyncio.sleep(0)` only yields to the event loop). Import aliases are "
        "followed; a local function, fixture or object method named `sleep` is not "
        "flagged. Fake or freeze the clock, or wait on the condition itself."
    ),
    bad_example=(
        "import time\n"
        "\n"
        "def test_token_expires():\n"
        "    token = issue_token(ttl=1)\n"
        "    time.sleep(1.1)\n"
        "    assert is_expired(token)\n"
    ),
    good_example=(
        "def test_token_expires():\n"
        "    clock = FakeClock()\n"
        "    token = issue_token(ttl=1, clock=clock)\n"
        "    clock.advance(1.1)\n"
        "    assert is_expired(token, clock=clock)\n"
    ),
    find=_find_sleep_in_test,
)


WALL_CLOCK_READ = Check(
    code="DS802",
    name="wall-clock-read",
    default_level=Level.FAIL,
    voice=(
        "What time is it, recruit? Time for you to stop asking the WALL CLOCK!",
        "This test passes at noon and fails at midnight! That's not a test, that's "
        "a SUNDIAL!",
        "The clock keeps moving, maggot! Freeze it or inject it!",
    ),
    why=(
        "A test that reads the real clock gives a different answer on each run, and "
        "fails at midnight, at month end, across a daylight-saving change or on a slow "
        "machine."
    ),
    explain=(
        "Flags a test that reads the wall clock: `time.time`, `time.time_ns`, "
        "`datetime.now`, `datetime.utcnow`, `datetime.today` or `date.today`, "
        "through any import alias. A read under a frozen clock is not flagged: in a "
        "test or class decorated with `freezegun.freeze_time`, `time_machine.travel` "
        "or `pytest.mark.freeze_time`, in a test that takes the `freezer` or "
        "`time_machine` fixture, or inside a `with freeze_time(...)` block. Use a "
        "fixed time or an injected clock, or freeze the clock."
    ),
    bad_example=(
        "from datetime import date, timedelta\n"
        "\n"
        "def test_invoice_is_due_in_thirty_days():\n"
        "    invoice = Invoice.issue()\n"
        "    assert invoice.due == date.today() + timedelta(days=30)\n"
    ),
    good_example=(
        "from datetime import date\n"
        "\n"
        "def test_invoice_is_due_in_thirty_days():\n"
        "    invoice = Invoice.issue(on=date(2026, 1, 1))\n"
        "    assert invoice.due == date(2026, 1, 31)\n"
    ),
    find=_find_wall_clock_read,
)


UNSEEDED_RANDOM = Check(
    code="DS803",
    name="unseeded-random",
    default_level=Level.FAIL,
    voice=(
        "Rolling dice in my barracks, recruit? Seed it or lose it!",
        "This test checks a different case every run! When it fails, NOBODY can "
        "make it fail again!",
        "Random without a seed is a coin toss with a stopwatch, maggot!",
    ),
    why=(
        "A test that draws unseeded random values checks a different case on every "
        "run, so it can fail at random and nobody can replay the failing case."
    ),
    explain=(
        "Flags a test that draws from the global `random` or `numpy.random` "
        "generator (`random.randint`, `random.shuffle`, `np.random.rand` and the "
        "like) with no seed, or builds `random.Random()`, "
        "`numpy.random.default_rng()` or `numpy.random.RandomState()` without one. "
        "A draw is seeded when the test itself, the module's top level or an autouse "
        "fixture in the file calls `random.seed(...)` (or `numpy.random.seed(...)`) "
        "with a value. Use fixed values, or a generator built with a seed."
    ),
    bad_example=(
        "import random\n"
        "\n"
        "def test_cart_total():\n"
        "    quantity = random.randint(1, 10)\n"
        "    assert Cart(quantity=quantity).total == quantity * 5\n"
    ),
    good_example=(
        "import random\n"
        "\n"
        "def test_cart_total():\n"
        "    quantity = random.Random(1234).randint(1, 10)\n"
        "    assert Cart(quantity=quantity).total == quantity * 5\n"
    ),
    find=_find_unseeded_random,
)
