"""The flakiness family (DS8xx): tests whose outcome rides on time or chance."""

import ast
from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from pytest_drill_sergeant.checks.ast_tools import (
    FIXTURE_DECORATORS,
    module_imports,
    qualified,
    value_params,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, Kind, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# The sleeps; each only yields, without waiting, when given a zero delay.
_SLEEPS = frozenset({"time.sleep", "asyncio.sleep", "trio.sleep", "anyio.sleep"})

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

# The `time` conversions that read the wall clock when given no timestamp.
_CLOCK_READS_WITHOUT_ARGS = frozenset({"time.localtime", "time.gmtime", "time.ctime"})

# What freezes the clock: as a decorator or `with`, and as a fixture a test takes.
_FREEZERS = frozenset(
    {"freezegun.freeze_time", "time_machine.travel", "pytest.mark.freeze_time"}
)
_FREEZER_FIXTURES = frozenset({"freezer", "time_machine"})

# The draws from a global generator, by the generator module whose seed governs
# them.
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


@dataclass(frozen=True)
class _Call:
    """A call in a test whose target an import reaches.

    Attributes:
        test: The test it is in.
        node: The call.
        target: What it calls, in full (`time.sleep`).
        names: The imported names the test sees, for resolving what's around it.
    """

    test: TestFunction
    node: ast.Call
    target: str
    names: Mapping[str, str]

    def hit(self, found: str, fix: str) -> Hit:
        """A hit on this call.

        `found` is followed by the call, and `fix` follows "replace `<call>` with ".
        """
        written = ast.unparse(self.node)
        return Hit.on(
            self.test,
            self.node.lineno,
            found=f"{found}: `{written}`.",
            fix=f"replace `{written}` with {fix}",
        )


def _calls(file: TestFile) -> Iterator[_Call]:
    """Every call in every test whose target an import reaches, in source order."""
    for test in file.tests:
        calls = [node for node in walk_test(test) if isinstance(node, ast.Call)]
        for call in sorted(calls, key=lambda c: (c.lineno, c.col_offset)):
            target = qualified(call.func, test.imports)
            if target:
                yield _Call(test, call, target, test.imports)


def _freezes(expr: ast.expr, names: Mapping[str, str]) -> bool:
    """Whether a decorator, `with` item or `pytestmark` entry freezes the clock."""
    target = expr.func if isinstance(expr, ast.Call) else expr
    return qualified(target, names) in _FREEZERS


def _module_frozen(module: ast.Module, names: Mapping[str, str]) -> bool:
    """Whether the module's `pytestmark` freezes the clock for every test."""
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in statement.targets
        ):
            value = statement.value
            marks = value.elts if isinstance(value, ast.List | ast.Tuple) else [value]
            if any(_freezes(mark, names) for mark in marks):
                return True
    return False


def _starts_freezer(test: TestFunction, names: Mapping[str, str]) -> bool:
    """Whether the test starts a freezer by hand (`freeze_time(...).start()`).

    The freezer may be held in a variable first, so any `.start()` call in a test
    that builds a freezer counts.
    """
    calls = [n for n in walk_test(test) if isinstance(n, ast.Call)]
    return any(_freezes(c, names) for c in calls) and any(
        isinstance(c.func, ast.Attribute) and c.func.attr == "start" for c in calls
    )


def _frozen_calls(
    file: TestFile, test: TestFunction, names: Mapping[str, str]
) -> set[ast.Call]:
    """The calls in a test that run under a frozen clock.

    All of them when the module's `pytestmark`, the test or a class around it
    freezes the clock, or the test takes a freezer fixture or starts a freezer by
    hand; otherwise those inside a freezer's `with`.
    """
    classes = [
        node
        for node in ast.walk(file.module)
        if isinstance(node, ast.ClassDef) and test.node in node.body
    ]
    decorators = [d for owner in [test.node, *classes] for d in owner.decorator_list]
    scopes: list[ast.AST] = []
    if (
        any(_freezes(d, names) for d in decorators)
        or value_params(test) & _FREEZER_FIXTURES
        or _module_frozen(file.module, names)
        or _starts_freezer(test, names)
    ):
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


# A function or lambda: code with its own scope, run only when something calls it.
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_Scope = ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda
_LOOPS = (ast.For, ast.AsyncFor, ast.While)

# Where in the file something happens: line, then column.
_Position = tuple[int, int]


def _own_nodes(scope: _Scope, *, into_classes: bool = True) -> Iterator[ast.AST]:
    """Every node of a function's or lambda's own code, at any depth.

    The functions and lambdas defined in it are yielded but not entered. Classes
    defined in it are entered, since their bodies run where they are defined,
    unless `into_classes` is false.
    """
    stack: list[ast.AST] = (
        [scope.body] if isinstance(scope, ast.Lambda) else list(reversed(scope.body))
    )
    closed = (*_SCOPES, ast.ClassDef) if not into_classes else _SCOPES
    while stack:
        node = stack.pop()
        yield node
        if not isinstance(node, closed):
            stack.extend(reversed(list(ast.iter_child_nodes(node))))


@dataclass(frozen=True)
class _Binding:
    """A name bound in a scope.

    Attributes:
        at: Where the binding takes effect.
        value: What the name is bound to: a def, class or lambda, a name it is an
            alias of, or `None` when the file doesn't show what it is.
    """

    at: _Position
    value: ast.AST | None


def _bindings(scope: _Scope) -> dict[str, list[_Binding]]:
    """The names a function or lambda binds in its own code, each binding in order.

    Its parameters are bound where it starts. What a class body or a
    comprehension binds is its own, not the function's.
    """
    start = (scope.lineno, scope.col_offset)
    found: dict[str, list[_Binding]] = {}
    for arg in ast.walk(scope.args):
        if isinstance(arg, ast.arg):
            found.setdefault(arg.arg, []).append(_Binding(start, None))
    nodes = list(_own_nodes(scope, into_classes=False))
    skipped = {
        id(name)
        for node in nodes
        if isinstance(node, ast.comprehension)
        for name in ast.walk(node.target)
    }
    for node in nodes:
        name = ""
        value: ast.AST | None = None
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            name, value = node.name, node
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            skipped.add(id(node.targets[0]))
            name, value = node.targets[0].id, node.value
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if id(node) in skipped:
                continue
            name = node.id
        elif isinstance(node, ast.alias):
            name = node.asname or node.name.partition(".")[0]
        else:
            continue
        end = (node.end_lineno or node.lineno, node.end_col_offset or 0)
        found.setdefault(name, []).append(_Binding(end, value))
    return found


class _TestRun:
    """The calls a test runs itself, outside any poll, following its own helpers.

    A function or lambda the test defines runs when a call the test runs calls
    the binding that holds it: `helper()`, `await helper()`, or as an argument
    such as `create_task(helper())`. A plain alias (`f = helper`) is followed, and
    the latest binding before the call is the one called, so `helper = other`
    hides the def. What the file doesn't show counts as not called: module-level
    helpers, methods, a stand-in handed over or set as an attribute. A helper
    called inside a poll is part of the poll.

    Attributes:
        calls: The calls run, outside any poll.
    """

    def __init__(self, test: TestFunction) -> None:
        self._parents: dict[int, _Scope] = {}
        self._bindings: dict[int, dict[str, list[_Binding]]] = {}
        self.calls: set[ast.Call] = set()
        running: set[int] = {id(test.node)}
        queue: list[_Scope] = [test.node]
        while queue:
            scope = queue.pop()
            nodes = list(_own_nodes(scope))
            for node in nodes:
                if isinstance(node, _SCOPES):
                    self._parents[id(node)] = scope
            polled = _polled(scope)
            for node in nodes:
                if not isinstance(node, ast.Call) or node in polled:
                    continue
                self.calls.add(node)
                called = self._called(node, scope)
                if called is not None and id(called) not in running:
                    running.add(id(called))
                    queue.append(called)

    def _called(self, call: ast.Call, scope: _Scope) -> _Scope | None:
        """The function or lambda of the test's own that a call runs, if any."""
        if isinstance(call.func, ast.Lambda):
            return call.func
        if not isinstance(call.func, ast.Name):
            return None
        target = self._resolve(call.func.id, (call.lineno, call.col_offset), scope)
        return target if isinstance(target, _SCOPES) else None

    def _resolve(self, name: str, at: _Position, scope: _Scope) -> ast.AST | None:
        """What a name holds at a position, by its latest binding before it.

        An alias is resolved where it was bound, always earlier, so it ends.
        """
        current: _Scope | None = scope
        while current is not None:
            key = id(current)
            if key not in self._bindings:
                self._bindings[key] = _bindings(current)
            earlier = [b for b in self._bindings[key].get(name, []) if b.at < at]
            if earlier:
                latest = max(earlier, key=lambda b: b.at)
                if isinstance(latest.value, ast.Name):
                    # An alias holds what its name held where it was bound.
                    return self._resolve(latest.value.id, latest.at, current)
                return latest.value
            current = self._parents.get(key)
        return None


def _leaves_early(loop: ast.For | ast.AsyncFor) -> bool:
    """Whether a `for` loop's body leaves it (`break` or `return`) under a condition.

    A `break` in a nested loop leaves only that loop; a `return` leaves them all.
    """

    def walk(statements: list[ast.stmt], *, into_loops: bool) -> Iterator[ast.AST]:
        closed = (
            (*_SCOPES, ast.ClassDef)
            if into_loops
            else (*_LOOPS, *_SCOPES, ast.ClassDef)
        )
        stack: list[ast.AST] = list(statements)
        while stack:
            node = stack.pop()
            yield node
            if not isinstance(node, closed):
                stack.extend(ast.iter_child_nodes(node))

    for branch in walk(loop.body, into_loops=True):
        if not isinstance(branch, ast.If):
            continue
        exits = [*branch.body, *branch.orelse]
        if any(isinstance(n, ast.Return) for n in walk(exits, into_loops=True)):
            return True
        if branch in walk(loop.body, into_loops=False) and any(
            isinstance(n, ast.Break) for n in walk(exits, into_loops=False)
        ):
            return True
    return False


def _polled(scope: _Scope) -> set[ast.Call]:
    """The calls inside a poll waiting on its condition.

    That is a `while` loop, or a `for` loop that leaves early under a condition.
    """
    return {
        node
        for loop in _own_nodes(scope)
        if isinstance(loop, ast.While)
        or (isinstance(loop, ast.For | ast.AsyncFor) and _leaves_early(loop))
        for node in ast.walk(loop)
        if isinstance(node, ast.Call)
    }


def _find_sleep_in_test(file: TestFile) -> Iterator[Hit]:
    # A frozen clock doesn't stop a sleep: freezegun and time-machine leave it real.
    # A sleep in a stand-in (a def, class or lambda the test hands over without
    # calling it) is the stand-in's behaviour, not the test's.
    runs: dict[int, set[ast.Call]] = {}
    for call in _calls(file):
        if call.target not in _SLEEPS or _is_zero(call.node):
            continue
        key = id(call.test.node)
        if key not in runs:
            runs[key] = _TestRun(call.test).calls
        if call.node not in runs[key]:
            continue
        yield call.hit(
            "sleeps for real time",
            "a fake clock it can advance, or wait on the condition itself (an event, "
            "a join, or a `while` loop that polls it under a deadline).",
        )


def _reads_clock(call: _Call) -> bool:
    """Whether a call reads the wall clock."""
    if call.target in _CLOCK_READS_WITHOUT_ARGS:
        return not (call.node.args or call.node.keywords)
    return call.target in _CLOCK_READS


def _find_wall_clock_read(file: TestFile) -> Iterator[Hit]:
    frozen: dict[str, set[ast.Call]] = {}
    for call in _calls(file):
        if not _reads_clock(call):
            continue
        if call.test.name not in frozen:
            frozen[call.test.name] = _frozen_calls(file, call.test, call.names)
        if call.node in frozen[call.test.name]:
            continue
        yield call.hit(
            "reads the wall clock",
            "a fixed time or an injected clock, or freeze the clock with "
            "`freezegun.freeze_time` or `time_machine.travel`.",
        )


def _generator_module(target: str) -> tuple[str, str]:
    """A call target split into generator module and function.

    Both are empty when the target isn't in `random` or `numpy.random`.
    """
    module, _, function = target.rpartition(".")
    return (module, function) if module in _DRAWS else ("", "")


def _seeds(
    nodes: list[ast.AST], names: Mapping[str, str], before: int | None = None
) -> set[str]:
    """The generator modules (`random`, `numpy.random`) the nodes seed with a value.

    `random.seed()` and `random.seed(None)` reseed from entropy, so they don't
    count. With `before`, only seeds on earlier lines count.
    """
    seeded: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if not isinstance(node, ast.Call) or (before and node.lineno >= before):
                continue
            values = [*node.args, *(k.value for k in node.keywords)]
            if all(isinstance(v, ast.Constant) and v.value is None for v in values):
                continue
            module, function = _generator_module(qualified(node.func, names) or "")
            if function == "seed":
                seeded.add(module)
    return seeded


def _is_autouse(decorator: ast.expr) -> bool:
    """Whether a fixture decorator says `autouse=True`."""
    return isinstance(decorator, ast.Call) and any(
        k.arg == "autouse" and isinstance(k.value, ast.Constant) and k.value.value
        for k in decorator.keywords
    )


def _fixtures(module: ast.Module, names: Mapping[str, str]) -> dict[str, bool]:
    """The file's module-level fixtures by name, each with whether it is autouse."""
    fixtures: dict[str, bool] = {}
    for node in module.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                target = (
                    decorator.func if isinstance(decorator, ast.Call) else decorator
                )
                if qualified(target, names) in FIXTURE_DECORATORS:
                    fixtures[node.name] = _is_autouse(decorator)
    return fixtures


def _find_unseeded_random(file: TestFile) -> Iterator[Hit]:
    names = module_imports(file.module)
    fixtures = _fixtures(file.module, names)
    defs: dict[str, ast.AST] = {
        node.name: node
        for node in file.module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    top_level: list[ast.AST] = [
        node
        for node in file.module.body
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
    ]
    autouse = [defs[name] for name, is_autouse in fixtures.items() if is_autouse]
    seeded_by_file = _seeds(top_level + autouse, names)
    for call in _calls(file):
        module, function = _generator_module(call.target)
        if function in _DRAWS.get(module, ()):
            requested = [
                defs[name] for name in value_params(call.test) if name in fixtures
            ]
            seeded = (
                seeded_by_file
                | _seeds(requested, names)
                | _seeds([call.test.node], call.names, before=call.node.lineno)
            )
            if module in seeded:
                continue
        elif call.target not in _GENERATORS or call.node.args or call.node.keywords:
            continue
        yield call.hit(
            "draws unseeded random values",
            "fixed values or a seeded generator (`random.Random(1234)`, "
            "`numpy.random.default_rng(1234)`).",
        )


SLEEP_IN_TEST = Check(
    code="DS801",
    name="sleep-in-test",
    kind=Kind.DEFECT,
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
        "Flags a test that calls `time.sleep`, `asyncio.sleep`, `trio.sleep` or "
        "`anyio.sleep` with a delay other than a literal zero (a zero sleep only "
        "yields). A sleep inside a `while` loop, or a `for` loop that leaves early "
        "(`break` or `return`) under a condition, is a poll waiting on its condition "
        "and is not flagged. A sleep inside a stand-in, a function, class or lambda "
        "the test defines and hands to the code under test without calling it "
        "itself, is the stand-in's behaviour and is not flagged; a never-set "
        "`asyncio.Event` (`await release.wait()`) is the cleaner way for one to "
        "stall. A helper the test defines and calls (`helper()`, `await helper()`, "
        "`create_task(helper())`, or through a plain alias) is the test sleeping and "
        "is flagged, unless it is called inside a poll; helpers defined outside the "
        "test are not followed. Import "
        "aliases are followed; a local function, fixture or object method named "
        "`sleep` is not flagged. Use a fake clock the test advances, or wait on the "
        "condition itself."
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
    kind=Kind.DEFECT,
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
        "`datetime.now`, `datetime.utcnow`, `datetime.today`, `date.today`, or "
        "`time.localtime`, `time.gmtime` or `time.ctime` with no timestamp, through "
        "any import alias. A read under a frozen clock is not flagged: in a module "
        "whose `pytestmark` freezes it, in a test or class decorated with "
        "`freezegun.freeze_time`, `time_machine.travel` or `pytest.mark.freeze_time`, "
        "in a test that takes the `freezer` or `time_machine` fixture or starts a "
        "freezer with `.start()`, or inside a `with freeze_time(...)` block. Use a "
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
    kind=Kind.DEFECT,
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
        "A draw is seeded when `random.seed(...)` (or `numpy.random.seed(...)`) is "
        "called with a value other than `None` at the module's top level, in an "
        "autouse fixture or a fixture the test takes in the same file, or earlier in "
        "the test itself. Seeds in `conftest.py` are not seen. Use fixed values, or "
        "a generator built with a seed."
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
