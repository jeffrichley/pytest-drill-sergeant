"""The mocking family (DS3xx): mocks that stand in for the behaviour under test.

A mock is known from what the files say, never from what a variable is called: a
call to `unittest.mock` (or the `mock` backport) resolved through the imports, a
call on a pytest-mock fixture the test takes (`mocker.patch(...)`), a parameter a
`patch` decorator hands in, or a name bound to any of those, an attribute of one,
or a call on one. `mock_db` taken as a fixture is not known to be a mock.

A parameter named for a pytest-mock fixture (`mocker`, `class_mocker` and the rest)
is that fixture only when the test's project declares pytest-mock among its
dependencies (`TestFile.dependencies`) and the test sees no fixture of that name
defined in the files: in its module, a class around it, or a `conftest.py` above
it. Without the declaration, the parameter is not known to be a mock.
"""

import ast
import builtins
from collections.abc import Iterator
from dataclasses import dataclass

from pytest_drill_sergeant.checks.ast_tools import (
    is_assert_call,
    is_real_assertion,
    positional_params,
    qualified,
    value_params,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, Kind, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# Where the mock library lives, by the prefix its names resolve to.
_MOCK_MODULES = ("unittest.mock.", "mock.")

# pytest-mock's fixtures, each a `MockerFixture` whose methods are the library's,
# and the package that provides them, as a declared dependency names it.
_MOCKER_FIXTURES = frozenset(
    {"mocker", "class_mocker", "module_mocker", "package_mocker", "session_mocker"}
)
_PYTEST_MOCK = "pytest-mock"

# The mock classes, which take a spec as their first argument or `spec=`.
_DOUBLES = frozenset(
    {"Mock", "MagicMock", "AsyncMock", "NonCallableMock", "NonCallableMagicMock"}
)

# The patchers that put a mock in place of a target, unless given what to put
# there: the position of their `new` argument.
_PATCHES = {"patch": 1, "patch.object": 2}

# What makes a mock that already carries the real interface.
_SPECCED = frozenset({"create_autospec", "spy"})

# The attributes that script what a mock does when it is called.
_SCRIPTING = frozenset({"return_value", "side_effect"})

# The arguments that give a mock the real interface.
_SPEC_ARGS = frozenset({"spec", "spec_set", "autospec"})


@dataclass(frozen=True)
class _Test:
    """A test as the mocking checks read it.

    Attributes:
        of: The test.
        mockers: The parameters it takes that are pytest-mock's fixtures.
    """

    of: TestFunction
    mockers: frozenset[str]


def _read(test: TestFunction, file: TestFile) -> _Test:
    """A test with the pytest-mock fixtures it takes.

    A parameter named for one is it when the project declares pytest-mock and the
    test sees no fixture of that name defined in the files.
    """
    if _PYTEST_MOCK not in file.dependencies:
        return _Test(test, frozenset())
    return _Test(
        test,
        frozenset(
            name
            for name in _MOCKER_FIXTURES & value_params(test)
            if not file.assertions.sees_fixture(test, name)
        ),
    )


def _mock_api(expr: ast.expr, test: _Test) -> str | None:
    """What a name stands for in the mock library (`Mock`, `patch.object`), if it does.

    Through the imports (`mock.patch` after `from unittest import mock`), or as a
    method of a pytest-mock fixture the test takes (`mocker.patch.object`).
    """
    full = qualified(expr, test.of.imports)
    if full is not None:
        for prefix in _MOCK_MODULES:
            if full.startswith(prefix):
                return full.removeprefix(prefix)
        return None
    parts: list[str] = []
    while isinstance(expr, ast.Attribute):
        parts.append(expr.attr)
        expr = expr.value
    if parts and isinstance(expr, ast.Name) and expr.id in test.mockers:
        return ".".join(reversed(parts))
    return None


def _given(call: ast.Call, keyword: str, position: int | None = None) -> bool:
    """Whether a call passes an argument, by keyword or at a position.

    A `**kwargs` spread may pass anything, so it counts as passing it.
    """
    if position is not None and len(call.args) > position:
        return True
    return any(k.arg in {keyword, None} for k in call.keywords)


def _replaces(call: ast.Call, api: str) -> bool:
    """Whether a patch call is told what to put in place, so makes no mock."""
    return _given(call, "new", _PATCHES[api])


def _makes_mock(call: ast.Call, test: _Test) -> bool:
    """Whether a call makes a mock or patches one in."""
    api = _mock_api(call.func, test)
    if api in _DOUBLES or api in _SPECCED:
        return True
    return api in _PATCHES and not _replaces(call, api)


def _patch_decorators(test: _Test) -> list[ast.Call]:
    """The test's decorators that patch a mock in and hand it to the test."""
    return [
        dec
        for dec in test.of.node.decorator_list
        if isinstance(dec, ast.Call)
        and _mock_api(dec.func, test) in _PATCHES
        and _makes_mock(dec, test)
    ]


def _bindings(node: ast.AST) -> Iterator[tuple[str, ast.expr]]:
    """The names a node binds to a value, each with the value."""
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                yield target.id, node.value
    elif isinstance(node, ast.AnnAssign | ast.NamedExpr):
        if isinstance(node.target, ast.Name) and node.value is not None:
            yield node.target.id, node.value
    elif isinstance(node, ast.With | ast.AsyncWith):
        for item in node.items:
            if isinstance(item.optional_vars, ast.Name):
                yield item.optional_vars.id, item.context_expr


class _Mocks:
    """What a test's code shows to be a mock."""

    def __init__(self, test: _Test) -> None:
        self.test = test
        injected = len(_patch_decorators(test))
        self.names = set(positional_params(test.of)[:injected])
        self.bound = value_params(test.of) | {
            n.id
            for n in walk_test(test.of)
            if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load)
        }
        changed = True
        while changed:
            changed = False
            for node in walk_test(test.of):
                for name, value in _bindings(node):
                    if name not in self.names and self.is_mock(value):
                        self.names.add(name)
                        changed = True

    def is_mock(self, expr: ast.expr) -> bool:
        """Whether an expression is a mock, an attribute of one or a call on one."""
        if isinstance(expr, ast.Name):
            return expr.id in self.names
        if isinstance(expr, ast.Attribute | ast.Subscript | ast.Await):
            return self.is_mock(expr.value)
        if isinstance(expr, ast.Call):
            return self.is_mock(expr.func) or _makes_mock(expr, self.test)
        return False

    def root(self, expr: ast.expr) -> str:
        """How to name the mock an expression starts from: its name, or its call."""
        while isinstance(expr, ast.Attribute | ast.Subscript | ast.Await):
            expr = expr.value
        if isinstance(expr, ast.Call):
            if self.is_mock(expr.func):
                return self.root(expr.func)
            first = f"{ast.unparse(expr.args[0])}, " if expr.args else ""
            return f"`{ast.unparse(expr.func)}({first}...)`"
        return f"`{ast.unparse(expr)}`"

    def configured_returns(self) -> dict[str, str]:
        """What the test told its mocks to return, each as its syntax tree dumped.

        Each maps to how to name the mock told to return it.
        """
        returns: dict[str, str] = {}
        nodes: list[ast.AST] = [*_patch_decorators(self.test), *walk_test(self.test.of)]
        for node in nodes:
            if isinstance(node, ast.Call) and _makes_mock(node, self.test):
                for k in node.keywords:
                    if k.arg == "return_value":
                        returns[ast.dump(k.value)] = self.root(node)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if self._is_return_value(target):
                        returns[ast.dump(node.value)] = self.root(target)
        return returns

    def _is_return_value(self, expr: ast.expr) -> bool:
        """Whether an expression is a mock's `return_value`."""
        return (
            isinstance(expr, ast.Attribute)
            and expr.attr == "return_value"
            and self.is_mock(expr.value)
        )

    def _neutral(self, expr: ast.expr) -> bool:
        """Whether an expression reads no value: a constant, or a library helper.

        A helper is the mock library's own (`mock.call`, `ANY`) or a builtin the
        test doesn't rebind (`len`).
        """
        if isinstance(expr, ast.Constant):
            return True
        if _mock_api(expr, self.test) is not None:
            return True
        return (
            isinstance(expr, ast.Name)
            and expr.id in vars(builtins)
            and expr.id not in self.test.of.imports
            and expr.id not in self.bound
        )

    def reads_only_mocks(self, expr: ast.expr) -> bool:
        """Whether an expression reads a mock and no other value."""
        mocks_read = False

        def visit(node: ast.expr) -> bool:
            nonlocal mocks_read
            if self.is_mock(node):
                mocks_read = True
                return True
            if self._neutral(node):
                return True
            if isinstance(node, ast.Name | ast.Attribute):
                return False
            return all(
                visit(child)
                for child in ast.iter_child_nodes(node)
                if isinstance(child, ast.expr)
            )

        return visit(expr) and mocks_read

    def echoed_mock(self, expr: ast.expr, returns: dict[str, str]) -> str | None:
        """The mock whose return value one side of an `==` or `is` is, named."""
        if not (
            isinstance(expr, ast.Compare)
            and len(expr.ops) == 1
            and isinstance(expr.ops[0], ast.Eq | ast.Is)
        ):
            return None
        for side in (expr.left, expr.comparators[0]):
            if self._is_return_value(side):
                return self.root(side)
            if ast.dump(side) in returns:
                return returns[ast.dump(side)]
        return None


def _mock_only_roots(
    node: ast.AST, mocks: _Mocks, returns: dict[str, str]
) -> list[str] | None:
    """The mocks a real assertion is about, or `None` if it checks anything else.

    That is a mock's own `assert*` method, an `assert` reading nothing but mocks
    (`send.call_count == 2`), or an `==` against what a mock was told to return.
    """
    if isinstance(node, ast.Call) and is_assert_call(node):
        func = node.func
        if isinstance(func, ast.Attribute) and mocks.is_mock(func.value):
            return [mocks.root(func.value)]
        return None
    if isinstance(node, ast.Assert):
        if mocks.reads_only_mocks(node.test):
            return [
                mocks.root(n)
                for n in ast.walk(node.test)
                if isinstance(n, ast.Name) and n.id in mocks.names
            ]
        echoed = mocks.echoed_mock(node.test, returns)
        if echoed is not None:
            return [echoed]
    return None


def _find_mock_only_assertion(file: TestFile) -> Iterator[Hit]:
    for function in file.tests:
        test = _read(function, file)
        mocks = _Mocks(test)
        returns = mocks.configured_returns()
        assertions = [
            n for n in walk_test(test.of) if is_real_assertion(n, test.of.imports)
        ]
        about = [_mock_only_roots(n, mocks, returns) for n in assertions]
        if not assertions or any(roots is None for roots in about):
            continue
        roots = list(dict.fromkeys(r for rs in about for r in rs or ()))
        named = ", ".join(roots)
        yield Hit.on(
            function,
            function.node.lineno,
            found=(
                f"asserts only on mocks ({named}): how they were called, or what "
                "they were told to return, never what the code under test returns "
                "or changes."
            ),
            fix=(
                "assert on what the code under test returns or changes, preferring a "
                f"fake you can inspect to {named}. If the call to {named} is itself "
                "the behaviour under test, ask the human for a waiver "
                "(`# drill: waive DS301 -- <reason>`); don't write one yourself."
            ),
        )


MOCK_ONLY_ASSERTION = Check(
    code="DS301",
    name="mock-only-assertion",
    kind=Kind.DEFECT,
    default_level=Level.FAIL,
    voice=(
        "You checked the mock got called! Did the MISSION succeed, recruit?!",
        "You told the mock what to say, then asserted it said it! Brilliant, maggot!",
        "This test is a MOCK-UP of a test! Check the OUTCOME, not the wiring!",
    ),
    why=(
        "A test that asserts only on mocks checks the wiring it set up itself, which "
        "calls were made or that a value it fed in came back, so it stays green "
        "when the behaviour breaks and goes red on a harmless refactor. The house "
        "rule is to mock only when the call itself is the behaviour; when it is, "
        "the human grants a waiver."
    ),
    explain=(
        "Flags a test whose every real assertion is about a mock: a mock's own "
        "`assert*` method (`assert_called_once_with`, `assert_called`), an `assert` "
        "reading nothing but mocks (`send.called`, `send.call_count == 2`), or an "
        "`==` or `is` against what a mock was told to return (`return_value`). A "
        "mock is known from the file: made by `unittest.mock` or a pytest-mock "
        "fixture such as `mocker`, or handed in by a `patch` decorator. A `mocker` "
        "parameter is pytest-mock's only when the project declares pytest-mock "
        "(in `pyproject.toml` or a `requirements` file) and no `mocker` fixture of "
        "its own, in the module or a `conftest.py`, takes its place. A name such "
        "as `mock_db` never makes a value one, so a mock built in a fixture isn't "
        "seen. Assert on what the code under test returns or changes, best through "
        "a fake you can inspect. Sometimes the call is the behaviour (an email sent, "
        "an event published): then ask the human for a waiver, "
        "`# drill: waive DS301 -- <reason>`, rather than writing one yourself."
    ),
    bad_example=(
        "from unittest import mock\n"
        "\n"
        "\n"
        "def test_get_customer():\n"
        "    repo = mock.create_autospec(Repo, instance=True)\n"
        "    repo.find_one.return_value = {'id': 1, 'name': 'Ada'}\n"
        "    assert CustomerService(repo).get(1) == {'id': 1, 'name': 'Ada'}\n"
        "    repo.find_one.assert_called_once_with(1)\n"
    ),
    good_example=(
        "def test_get_customer_formats_the_display_name():\n"
        "    repo = InMemoryRepo([{'id': 1, 'first': 'Ada', 'last': 'Lovelace'}])\n"
        "    assert CustomerService(repo).get(1).display_name == 'Ada Lovelace'\n"
    ),
    find=_find_mock_only_assertion,
)


def _without_spec(call: ast.Call, test: _Test) -> bool:
    """Whether a call makes a mock that accepts any attribute and any signature.

    That is a mock class given no spec (first argument, `spec` or `spec_set`), or
    a patch that makes its mock with no `autospec`, `spec`, `spec_set` or
    `new_callable`.
    """
    api = _mock_api(call.func, test)
    if api in _DOUBLES:
        return not call.args and not any(_given(call, arg) for arg in _SPEC_ARGS)
    if api in _PATCHES and _makes_mock(call, test):
        return not any(_given(call, arg) for arg in (*_SPEC_ARGS, "new_callable"))
    return False


def _find_mock_without_spec(file: TestFile) -> Iterator[Hit]:
    for function in file.tests:
        test = _read(function, file)
        nodes = [*function.node.decorator_list, *walk_test(function)]
        calls = [n for n in nodes if isinstance(n, ast.Call) and _without_spec(n, test)]
        for call in sorted(calls, key=lambda c: (c.lineno, c.col_offset)):
            written = ast.unparse(call)
            api = _mock_api(call.func, test)
            remedy = (
                "pass `autospec=True`, so the mock it puts in place has the real "
                "target's attributes and signature"
                if api in _PATCHES
                else "build it from the real class, `mock.create_autospec(<Real>, "
                "instance=True)`, or pass `spec=<Real>`, so a call the real object "
                "doesn't support fails"
            )
            yield Hit.on(
                function,
                call.lineno,
                found=f"makes a mock with no spec: `{written}`.",
                fix=f"in `{written}`, {remedy}.",
            )


MOCK_WITHOUT_SPEC = Check(
    code="DS302",
    name="mock-without-spec",
    kind=Kind.SMELL,
    default_level=Level.OFF,
    voice=(
        "A mock with no spec answers to ANY order! That's not a soldier, that's a ghost!",
        "Your mock would salute a method that doesn't EXIST, recruit! Give it a spec!",
        "The real interface changed and your mock never noticed! SPEC IT, maggot!",
    ),
    why=(
        "A mock with no spec accepts any attribute and any call, so the test stays "
        "green when the real interface changes or when the code calls a method that "
        "doesn't exist."
    ),
    explain=(
        "Flags a mock made with no spec: `Mock()`, `MagicMock()`, `AsyncMock()`, "
        "`NonCallableMock()` or `NonCallableMagicMock()` with no first argument, "
        "`spec` or `spec_set`, and a `patch` or `patch.object` (as a decorator, a "
        "`with`, or `mocker.patch`) that makes its mock with no `autospec`, `spec`, "
        "`spec_set` or `new_callable`. A patch told what to put in place (`new`) "
        "makes no mock, and `create_autospec` and `mocker.spy` carry the real "
        "interface. Only the mock library counts, known from the imports or a "
        "pytest-mock fixture the test takes (as DS301 knows one); a `Mock` from "
        "elsewhere doesn't. Build "
        "the mock with `create_autospec(<Real>, instance=True)` or `spec=<Real>`, "
        "and patch with `autospec=True`. Off by default until it is proven; turn "
        "it on with `drill_sergeant_levels` (`DS302=warn`). It warns rather than "
        "fails: "
        "a bare `Mock()` standing in for a callback or a sentinel has no real "
        "interface to copy."
    ),
    bad_example=(
        "from unittest import mock\n"
        "\n"
        "\n"
        "def test_process_payment_reports_ok():\n"
        "    gateway = mock.MagicMock()\n"
        "    gateway.charge.return_value = {'status': 'ok'}\n"
        "    assert PaymentHandler(gateway).process(100).status == 'ok'\n"
    ),
    good_example=(
        "from unittest import mock\n"
        "\n"
        "\n"
        "def test_process_payment_reports_ok():\n"
        "    gateway = mock.create_autospec(Gateway, instance=True)\n"
        "    gateway.charge.return_value = {'status': 'ok'}\n"
        "    assert PaymentHandler(gateway).process(100).status == 'ok'\n"
    ),
    find=_find_mock_without_spec,
)


def _patch_target(call: ast.Call, api: str) -> str:
    """How a patch call names what it patches: its target, as the file writes it.

    Positional or by keyword (`target`, `attribute`).
    """
    names = ("target", "attribute") if api == "patch.object" else ("target",)
    taken = [*call.args[: len(names)]]
    taken += [k.value for k in call.keywords if k.arg in names[len(taken) :]]
    return f"{api}({', '.join(ast.unparse(a) for a in taken)})"


class _Setup:
    """A test's mock setup: each target it scripts, with the line it is first set up.

    A target is a mock's name with its attribute path (`repo.get.return_value`), or
    a patch's target (`patch('shop.clock')`), so rebuilding it in a later phase
    sets up nothing new.
    """

    def __init__(self, test: _Test) -> None:
        self.test = test
        self.mocks = _Mocks(test)
        self.targets: dict[str, int] = {}
        for dec in test.of.node.decorator_list:
            if isinstance(dec, ast.Call):
                self._patches(dec, dec.lineno)
        for node in walk_test(test.of):
            if isinstance(node, ast.With | ast.AsyncWith):
                for item in node.items:
                    self._made(item.context_expr, item.optional_vars)
            elif isinstance(node, ast.Assign | ast.AnnAssign):
                targets = (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
                for target in targets:
                    if node.value is not None:
                        self._assigned(target, node.value, node.lineno)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                self._called(node.value)

    def _add(self, target: str, line: int) -> None:
        self.targets.setdefault(target, line)

    def _patches(self, call: ast.Call, line: int) -> bool:
        """Count a patch that makes a mock, or `patch.multiple`'s `DEFAULT`s."""
        api = _mock_api(call.func, self.test)
        if api in _PATCHES and _makes_mock(call, self.test):
            self._add(_patch_target(call, api), line)
            return True
        if api == "patch.multiple" and call.args:
            where = ast.unparse(call.args[0])
            for k in call.keywords:
                if k.arg is not None and _mock_api(k.value, self.test) == "DEFAULT":
                    self._add(f"{where}.{k.arg}", line)
            return True
        return False

    def _made(self, value: ast.expr, bound: ast.expr | None) -> None:
        """Count a value that makes a mock, as its patch target or the name it is bound to."""
        if not isinstance(value, ast.Call) or self._patches(value, value.lineno):
            return
        if bound is not None and _makes_mock(value, self.test):
            self._add(ast.unparse(bound), value.lineno)

    def _assigned(self, target: ast.expr, value: ast.expr, line: int) -> None:
        """Count an assignment that makes a mock or scripts one."""
        if isinstance(target, ast.Name):
            self._made(value, target)
        elif self.mocks.is_mock(target) and (
            (isinstance(target, ast.Attribute) and target.attr in _SCRIPTING)
            or self._a_mock(value)
        ):
            self._add(ast.unparse(target), line)

    def _a_mock(self, value: ast.expr) -> bool:
        """Whether a value is a mock in itself: one made there, or a name bound to one.

        An attribute of a mock (`info.uuid`) read and assigned on is a value copied,
        not a mock set up.
        """
        if isinstance(value, ast.Name):
            return value.id in self.mocks.names
        return isinstance(value, ast.Call) and _makes_mock(value, self.test)

    def _called(self, call: ast.Call) -> None:
        """Count a bare patch call, or a mock's own method that scripts it."""
        if self._patches(call, call.lineno):
            return
        func = call.func
        if not (isinstance(func, ast.Attribute) and self.mocks.is_mock(func.value)):
            return
        owner = ast.unparse(func.value)
        if func.attr == "attach_mock" and len(call.args) > 1:
            name = call.args[1]
            if isinstance(name, ast.Constant) and isinstance(name.value, str):
                self._add(f"{owner}.{name.value}", call.lineno)
        elif func.attr == "configure_mock":
            for path, value in _configured(call):
                if path.rsplit(".", 1)[-1] in _SCRIPTING or self._a_mock(value):
                    self._add(f"{owner}.{path}", call.lineno)


def _configured(call: ast.Call) -> Iterator[tuple[str, ast.expr]]:
    """The attribute paths a `configure_mock` call sets, each with its value.

    By keyword, or as the string keys of a dict literal spread with `**`.
    """
    for k in call.keywords:
        if k.arg is not None:
            yield k.arg, k.value
        elif isinstance(k.value, ast.Dict):
            for key, value in zip(k.value.keys, k.value.values, strict=True):
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    yield key.value, value


def _find_overgrown_mock_setup(file: TestFile) -> Iterator[Hit]:
    limit = file.thresholds.max_mock_setup
    for function in file.tests:
        targets = _Setup(_read(function, file)).targets
        if len(targets) <= limit:
            continue
        where = ", ".join(str(n) for n in sorted(set(targets.values())))
        yield Hit.on(
            function,
            function.node.lineno,
            found=(
                f"sets up {len(targets)} mock targets, more than the {limit} "
                "allowed: it scripts its collaborators' calls instead of using them."
            ),
            fix=(
                f"replace the mocks set up on lines {where} with a fake of each "
                "collaborator, built once in a fixture, or test one level up with "
                "real objects."
            ),
        )


OVERGROWN_MOCK_SETUP = Check(
    code="DS303",
    name="overgrown-mock-setup",
    kind=Kind.SMELL,
    default_level=Level.WARN,
    voice=(
        "More mock setup than test! You're writing a SCREENPLAY, recruit!",
        "Twenty lines of rehearsal for one line of combat! Use a fake, maggot!",
        "This test scripts every call the code makes! Change one and it COLLAPSES!",
    ),
    why=(
        "A test buried in mock setup restates the implementation's call sequence, "
        "so it breaks on any refactor, stays green when the real collaborators "
        "change, and hides what it checks."
    ),
    explain=(
        "Flags a test that sets up more mock targets than "
        "`drill_sergeant_max_mock_setup` (5 by default). A target is a mock's name "
        "with its attribute path, or a patch's target, counted once however often a "
        "later phase rebuilds it. Setup is a mock made and bound to a name "
        "(`repo = Mock(...)`, `create_autospec(...)`), a `patch` that makes a mock "
        "(a decorator, a `with` item or `mocker.patch(...)`), a mock's `return_value` "
        "or `side_effect` set (`repo.get.return_value = ...`), and a mock's attribute "
        "assigned a mock (`repo.close = AsyncMock()`, `configure_mock`, "
        "`attach_mock`). A plain value assigned to a mock's attribute is data, not "
        "setup, and so is one copied from another mock's attribute; `reset_mock()`, "
        "calling a mock and a patch given `new` set up nothing. A mock is known from "
        "the file, as DS301 knows it: a fixture named `mock_repo` isn't one, and "
        "setup in a fixture doesn't count against the test. Replace the mocks with "
        "fakes built once in a fixture, or test one level up with real objects. It "
        "warns rather than fails: a test of glue code may need several mocks."
    ),
    bad_example=(
        "from unittest import mock\n"
        "\n"
        "\n"
        "def test_checkout_total():\n"
        "    repo = mock.create_autospec(Repo, instance=True)\n"
        "    gateway = mock.create_autospec(Gateway, instance=True)\n"
        + "".join(f"    repo.find_{n}.return_value = {n}\n" for n in range(4))
        + "    assert Checkout(repo, gateway).run(cart_id=7).total == 1350\n"
    ),
    good_example=(
        "def test_checkout_total(fake_repo, fake_gateway):\n"
        "    receipt = Checkout(fake_repo, fake_gateway).run(cart_id=7)\n"
        "    assert receipt.total == 1350\n"
    ),
    find=_find_overgrown_mock_setup,
)
