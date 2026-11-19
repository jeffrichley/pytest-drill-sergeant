"""The syntax questions every check family asks, answered once.

What a call is named, what a name stands for through the file's imports, which
parameters bring a test its values, which nodes are a test's own code, and what a
real assertion and what cleanup is.
"""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.base import FunctionNode, TestFunction

# pytest's helpers that fail the test: `pytest.fail`, and the context managers that
# require an exception or warning.
_PYTEST_ASSERTING = frozenset(
    {"pytest.fail", "pytest.raises", "pytest.warns", "pytest.deprecated_call"}
)
PYTEST_RAISES = frozenset({"pytest.raises"})

# The decorators that make a function a fixture, which pytest never collects.
FIXTURE_DECORATORS = frozenset({"pytest.fixture", "pytest_asyncio.fixture"})


# Methods called for cleanup, reset or output, never the act under test.
_NOT_AN_ACT = frozenset(
    {
        "cleanup",
        "close",
        "disconnect",
        "print",
        "reset_mock",
        "rmtree",
        "shutdown",
        "stop",
        "teardown",
        "unlink",
    }
)

# pytest's capture fixtures' resets and setup, as (fixture, method): they ready the
# fixture for the next act rather than act themselves.
_FIXTURE_RESETS = frozenset(
    {
        ("caplog", "clear"),
        ("caplog", "set_level"),
        ("recwarn", "clear"),
        ("capsys", "readouterr"),
        ("capfd", "readouterr"),
    }
)

# Functions that clean up files, named in full.
_CLEANUP_FUNCTIONS = frozenset({"os.remove", "os.unlink", "shutil.rmtree"})

# A logger's methods: output, never the act under test.
_LOG_METHODS = frozenset(
    {"debug", "info", "warning", "error", "exception", "critical", "log"}
)


def call_name(call: ast.Call) -> str | None:
    """The name a call is made by: `f` for `f(...)` and `obj.f(...)`."""
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    return func.id if isinstance(func, ast.Name) else None


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


def _bound_names(statement: ast.stmt) -> Iterator[str]:
    """The names a statement binds where it stands, imports aside.

    That is a `def` or `class`, an assignment, a `for` target or a `with ... as`.
    """
    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        yield statement.name
        return
    targets: list[ast.expr] = []
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign | ast.For | ast.AsyncFor):
        targets = [statement.target]
    elif isinstance(statement, ast.With | ast.AsyncWith):
        targets = [i.optional_vars for i in statement.items if i.optional_vars]
    for target in targets:
        for node in ast.walk(target):
            if isinstance(node, ast.Name):
                yield node.id


def module_imports(module: ast.Module) -> dict[str, str]:
    """The names a module binds by import at its top level, minus any it rebinds.

    Each maps to what it stands for in full: `pt` to `pytest` after `import pytest
    as pt`, `raises` to `pytest.raises` after `from pytest import raises`. Imports
    under a top-level `if` or `try` count, and a fallback there (`np = None` after
    `except ImportError`) doesn't undo them; a later top-level `def`, `class` or
    assignment of the same name wins, as it does at run time.
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


def value_params(node: FunctionNode) -> set[str]:
    """A test's value parameters: the fixtures and parameters it takes.

    `self` and `cls` are the test's own class, not values handed in.
    """
    return {arg.arg for arg in ast.walk(node.args) if isinstance(arg, ast.arg)} - {
        "self",
        "cls",
    }


def imports_seen_by(
    node: FunctionNode, module_names: Mapping[str, str]
) -> dict[str, str]:
    """The imported names a test sees: the module's, its own imports, minus shadows.

    A parameter (a fixture) or a name the test binds itself, such as a nested
    `def sleep`, hides the module's import of the same name.
    """
    names = dict(module_names)
    shadows = value_params(node)
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, ast.Import | ast.ImportFrom):
            _bind_imports(child, names)
        elif isinstance(child, ast.stmt):
            shadows.update(_bound_names(child))
    for shadow in shadows:
        names.pop(shadow, None)
    return names


def qualified(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """What an expression names through the imports in scope, or `None`.

    `t.sleep` is `time.sleep` after `import time as t`; a name no import reaches is
    `None`.
    """
    if isinstance(expr, ast.Name):
        return names.get(expr.id)
    if isinstance(expr, ast.Attribute):
        base = qualified(expr.value, names)
        return f"{base}.{expr.attr}" if base else None
    return None


def calls_to(node: ast.AST, targets: frozenset[str], names: Mapping[str, str]) -> bool:
    """Whether a node is a call to one of the targets, named in full."""
    return isinstance(node, ast.Call) and qualified(node.func, names) in targets


def walk_test(test: TestFunction) -> Iterator[ast.AST]:
    """Every node of a test's own code: its body, at any depth.

    A helper function, class or lambda defined in the test is part of it, so its
    nodes count; the test's decorators and parameter defaults don't.
    """
    for statement in test.node.body:
        yield from ast.walk(statement)


def is_always_true(test: ast.expr) -> bool:
    """Whether an `assert`'s test is a truthy constant or a non-empty tuple."""
    if isinstance(test, ast.Constant):
        return bool(test.value)
    return isinstance(test, ast.Tuple) and bool(test.elts)


def is_assert_call(node: ast.AST) -> bool:
    """Whether a node is an `assert*`-named call.

    That is a mock verification, a unittest
    assertion or a helper such as `assert_frame_equal`.
    """
    if not isinstance(node, ast.Call):
        return False
    name = call_name(node)
    return name is not None and name.lower().startswith("assert")


def is_real_assertion(node: ast.AST, names: Mapping[str, str]) -> bool:
    """Whether a node can fail the test on the outcome it checks.

    An `assert` of anything but a truthy constant or non-empty tuple counts, and so
    does a call to `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or
    `pytest.fail` (through whatever name the imports give it), any `assert*` call,
    and raising `AssertionError`.

    Args:
        node: The node.
        names: The imported names in scope, as `imports_seen_by` gives them.
    """
    if isinstance(node, ast.Assert):
        return not is_always_true(node.test)
    if isinstance(node, ast.Call):
        return calls_to(node, _PYTEST_ASSERTING, names) or is_assert_call(node)
    if isinstance(node, ast.Raise) and node.exc is not None:
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        return isinstance(exc, ast.Name) and exc.id == "AssertionError"
    return False


def excinfo_names(test: TestFunction) -> set[str]:
    """The names a test binds to what `pytest.raises` caught (`with ... as e`)."""
    return {
        item.optional_vars.id
        for node in walk_test(test)
        if isinstance(node, ast.With | ast.AsyncWith)
        for item in node.items
        if isinstance(item.optional_vars, ast.Name)
        and calls_to(item.context_expr, PYTEST_RAISES, test.imports)
    }


def _is_logging(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call logs.

    That is a logger method on `logging`, `logging.getLogger(...)`,
    or a name with `log` in it (`log`, `logger`, `self.log`).
    """
    func = call.func
    if not (isinstance(func, ast.Attribute) and func.attr in _LOG_METHODS):
        return False
    receiver = func.value
    if isinstance(receiver, ast.Call):
        receiver = receiver.func
    full = qualified(receiver, names) or ""
    written = receiver.attr if isinstance(receiver, ast.Attribute) else ""
    if isinstance(receiver, ast.Name):
        written = receiver.id
    return full.startswith("logging") or "log" in written.lower()


def is_cleanup(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call cleans up, resets or reports rather than acting."""
    return (
        call_name(call) in _NOT_AN_ACT
        or (
            isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and (call.func.value.id, call.func.attr) in _FIXTURE_RESETS
        )
        or qualified(call.func, names) in _CLEANUP_FUNCTIONS
        or _is_logging(call, names)
    )
