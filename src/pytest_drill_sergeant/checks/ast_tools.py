"""The syntax questions every check family asks, answered once.

What a call is named, what a name stands for through the file's imports, which
parameters bring a test its values, which nodes are a test's own code, what a real
assertion is, and what a call is known to be: cleanup, output or a pytest
instrument.

Known means from what the file says: a name resolved through its imports, a
top-level assignment traced to its call, or a pytest built-in fixture the test takes
as a parameter. Never from what a variable or method is called: `logger`, `close`
or `expected` is the author's word, not the code's.
"""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.base import FunctionNode, TestFunction
from pytest_drill_sergeant.findings import MODULE

# pytest's helpers that fail the test: `pytest.fail`, and the context managers that
# require an exception or warning.
_PYTEST_ASSERTING = frozenset(
    {"pytest.fail", "pytest.raises", "pytest.warns", "pytest.deprecated_call"}
)
PYTEST_RAISES = frozenset({"pytest.raises"})

# The keyword that names the class `pytest.raises` or `pytest.warns` expects, when
# the first positional argument doesn't.
_EXPECTED_CLASS_KEYWORD = {
    "pytest.raises": "expected_exception",
    "pytest.warns": "expected_warning",
}

# pytest-check's helpers, each of which fails the test when its check doesn't hold,
# reached through the module or its `check` object.
_PYTEST_CHECK_HELPERS = (
    "equal",
    "not_equal",
    "is_",
    "is_not",
    "is_true",
    "is_false",
    "is_none",
    "is_not_none",
    "is_nan",
    "is_not_nan",
    "is_in",
    "is_not_in",
    "is_instance",
    "is_not_instance",
    "almost_equal",
    "not_almost_equal",
    "greater",
    "greater_equal",
    "less",
    "less_equal",
    "between",
    "between_equal",
    "raises",
    "fail",
)
_PYTEST_CHECK_ASSERTING = frozenset(
    f"{owner}.{helper}"
    for owner in ("pytest_check", "pytest_check.check", "pytest_check.check_functions")
    for helper in _PYTEST_CHECK_HELPERS
)

# Playwright's `expect`: a matcher called on what it returns
# (`expect(page).to_have_title(...)`) fails the test.
_EXPECT_FUNCTIONS = frozenset(
    {"playwright.sync_api.expect", "playwright.async_api.expect"}
)

# The decorators that make a function a fixture, which pytest never collects.
FIXTURE_DECORATORS = frozenset({"pytest.fixture", "pytest_asyncio.fixture"})


# pytest's built-in fixtures that are the test's own instruments: a call on one,
# taken as a test parameter, readies or reads the instrument, never acts.
_PYTEST_INSTRUMENTS = frozenset(
    {
        "caplog",
        "capsys",
        "capfd",
        "capsysbinary",
        "capfdbinary",
        "recwarn",
        "monkeypatch",
    }
)

# Functions that clean up files, named in full.
_CLEANUP_FUNCTIONS = frozenset({"os.remove", "os.unlink", "shutil.rmtree"})

# What `logging.getLogger(...)` returns, as a name it is known by.
_LOGGER = "logging.Logger"

# A logger's methods, on `logging` itself or on a logger: output, never an act.
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


def bound_names(statement: ast.stmt) -> Iterator[str]:
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


def _logger_bound_by(statement: ast.stmt, names: Mapping[str, str]) -> str | None:
    """The name a `name = logging.getLogger(...)` statement binds, if it is one."""
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and _known_as(statement.value, names) == _LOGGER
    ):
        return statement.targets[0].id
    return None


def module_imports(module: ast.Module) -> dict[str, str]:
    """The names a module binds by import at its top level, minus any it rebinds.

    Each maps to what it stands for in full: `pt` to `pytest` after `import pytest
    as pt`, `raises` to `pytest.raises` after `from pytest import raises`. Imports
    under a top-level `if` or `try` count, and a fallback there (`np = None` after
    `except ImportError`) doesn't undo them; a later top-level `def`, `class` or
    assignment of the same name wins, as it does at run time. A top-level
    `log = logging.getLogger(...)` binds `log` to `logging.Logger`, what the call
    returns.
    """
    names: dict[str, str] = {}
    for statement in module.body:
        if isinstance(statement, ast.If | ast.Try):
            for node in ast.walk(statement):
                if isinstance(node, ast.Import | ast.ImportFrom):
                    _bind_imports(node, names)
        elif isinstance(statement, ast.Import | ast.ImportFrom):
            _bind_imports(statement, names)
        elif (logger := _logger_bound_by(statement, names)) is not None:
            names[logger] = _LOGGER
        else:
            for bound in bound_names(statement):
                names.pop(bound, None)
    return names


def _param_names(node: FunctionNode | ast.Lambda) -> list[str]:
    """Every parameter a function takes, in order, positional ones first."""
    args = node.args
    starred = [a for a in (args.vararg, args.kwarg) if a is not None]
    return [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs + starred]


def instance_param(test: TestFunction) -> str | None:
    """The parameter a test in a class takes its instance by; `None` at module level.

    It is the first positional parameter, whatever it is called.
    """
    args = test.node.args
    positional = args.posonlyargs + args.args
    return positional[0].arg if test.classes and positional else None


def positional_params(test: TestFunction) -> list[str]:
    """The test's positional parameters in order, without its instance."""
    args = test.node.args
    params = [a.arg for a in args.posonlyargs + args.args]
    return params[1:] if instance_param(test) is not None else params


def value_params(test: TestFunction) -> set[str]:
    """A test's value parameters: the fixtures and parameters it takes.

    A test in a class takes its instance first, whatever the parameter is
    called; that is the test's own object, not a value handed in. At module
    level every parameter is one, `self` and `cls` included.
    """
    return set(_param_names(test.node)) - {instance_param(test)}


def imports_seen_by(
    node: FunctionNode, module_names: Mapping[str, str]
) -> dict[str, str]:
    """The imported names a test sees: the module's, its own imports, minus shadows.

    A parameter (a fixture), a nested function's or lambda's parameter, or a name
    the test binds itself, such as a nested `def sleep`, hides the module's import
    of the same name.
    """
    names = dict(module_names)
    shadows = set(_param_names(node))
    for child in ast.walk(node):
        if child is node:
            continue
        if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
            shadows.update(_param_names(child))
        if isinstance(child, ast.Import | ast.ImportFrom):
            _bind_imports(child, names)
        elif isinstance(child, ast.stmt):
            shadows.update(bound_names(child))
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


def expected_class(call: ast.Call, names: Mapping[str, str]) -> ast.expr | None:
    """The exception or warning class a `pytest.raises` or `pytest.warns` call expects.

    It is the call's first positional argument, or its `expected_exception` (for
    `pytest.raises`) or `expected_warning` (for `pytest.warns`) keyword; `None` for
    any other call, or one that names no class.

    Args:
        call: The call.
        names: The imported names in scope, as `imports_seen_by` gives them.
    """
    keyword = _EXPECTED_CLASS_KEYWORD.get(qualified(call.func, names) or "")
    if keyword is None:
        return None
    if call.args:
        return call.args[0]
    return next((k.value for k in call.keywords if k.arg == keyword), None)


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


def _is_expect_matcher(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call is a matcher on Playwright's `expect(...)`, known by import."""
    func = call.func
    return isinstance(func, ast.Attribute) and calls_to(
        func.value, _EXPECT_FUNCTIONS, names
    )


def is_real_assertion(node: ast.AST, names: Mapping[str, str]) -> bool:
    """Whether a node can fail the test on the outcome it checks.

    An `assert` of anything but a truthy constant or non-empty tuple counts, and so
    does a call to `pytest.raises`, `pytest.warns`, `pytest.deprecated_call` or
    `pytest.fail` (through whatever name the imports give it), any `assert*` call,
    a call made through an assertion library the imports reach (a pytest-check
    helper such as `check.equal`, a matcher on Playwright's `expect(...)`), and
    raising `AssertionError`.

    Args:
        node: The node.
        names: The imported names in scope, as `imports_seen_by` gives them.
    """
    if isinstance(node, ast.Assert):
        return not is_always_true(node.test)
    if isinstance(node, ast.Call):
        return (
            calls_to(node, _PYTEST_ASSERTING | _PYTEST_CHECK_ASSERTING, names)
            or is_assert_call(node)
            or _is_expect_matcher(node, names)
        )
    if isinstance(node, ast.Raise) and node.exc is not None:
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        return isinstance(exc, ast.Name) and exc.id == "AssertionError"
    return False


def own_statements(test: TestFunction) -> list[ast.stmt]:
    """A test's own statements, in order, its docstring aside."""
    body = test.node.body
    return body[1:] if ast.get_docstring(test.node) is not None else body


def setup(test: TestFunction) -> list[ast.stmt]:
    """A test's setup: its statements before the first that holds a real assertion.

    The docstring is set aside (`own_statements`); a test with no real assertion
    is all setup.
    """
    statements = own_statements(test)
    for index, statement in enumerate(statements):
        if any(is_real_assertion(node, test.imports) for node in ast.walk(statement)):
            return statements[:index]
    return statements


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


def _known_as(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """What an expression is known to be, named in full, or `None`.

    A name or attribute is what the imports make it (`qualified`); a call to
    `logging.getLogger` is `logging.Logger`, what it returns.
    """
    if isinstance(expr, ast.Call):
        return _LOGGER if qualified(expr.func, names) == "logging.getLogger" else None
    return qualified(expr, names)


def _logs(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call is a logger method on `logging` or on a known logger."""
    func = call.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr in _LOG_METHODS
        and _known_as(func.value, names) in {"logging", _LOGGER}
    )


def _prints(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call is the builtin `print`, which no import rebinds."""
    return (
        isinstance(call.func, ast.Name)
        and call.func.id == "print"
        and "print" not in names
    )


def _uses_a_pytest_instrument(call: ast.Call, test: TestFunction) -> bool:
    """Whether a call is a method of a pytest built-in fixture the test takes."""
    receiver = call.func.value if isinstance(call.func, ast.Attribute) else None
    return (
        isinstance(receiver, ast.Name)
        and receiver.id in _PYTEST_INSTRUMENTS
        and receiver.id in value_params(test)
    )


def is_known_non_act(call: ast.Call, test: TestFunction) -> bool:
    """Whether a call is known to be output or a pytest instrument, never an act.

    Known means from what the file says, never from what a name suggests: a call
    resolved through the imports (`logging.info`, the builtin `print`), a logger
    traced to a top-level `logging.getLogger(...)`, or a method of a pytest built-in
    fixture the test takes as a parameter (`caplog.clear()`, `capsys.readouterr()`).
    A name such as `logger`, or a method such as `close`, is the author's word, not
    the code's, so it counts for nothing.
    """
    return (
        _logs(call, test.imports)
        or _prints(call, test.imports)
        or _uses_a_pytest_instrument(call, test)
    )


def is_cleanup(call: ast.Call, names: Mapping[str, str]) -> bool:
    """Whether a call is known to clean up files.

    That is `os.remove`, `os.unlink` or `shutil.rmtree`, resolved through the
    imports, never guessed from a name.
    """
    return qualified(call.func, names) in _CLEANUP_FUNCTIONS


# How pytest joins a test's classes and its name: `TestX::test_y`.
TEST_PATH = "::"


def inside(where: str, name: str, separator: str) -> str:
    """The name of a function or class defined in a place (`MODULE` or a name).

    `Parser.parse` with `.`, `TestX::test_y` with `TEST_PATH`; at module level, the
    name alone.
    """
    return name if where == MODULE else f"{where}{separator}{name}"


# pytest's marks that skip a test, or expect it to fail.
SKIP = "pytest.mark.skip"
SKIPIF = "pytest.mark.skipif"
XFAIL = "pytest.mark.xfail"
_SKIP_MARKS = frozenset({SKIP, SKIPIF, XFAIL})

# pytest's calls that skip a test, or mark it an expected failure, as it runs.
SKIP_CALL = "pytest.skip"
XFAIL_CALL = "pytest.xfail"


def mark_name(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """What a decorator or `pytestmark` entry names in full, called or not, or `None`.

    `m.unit()` is `pytest.mark.unit` after `from pytest import mark as m`; a mark no
    import reaches is `None`.
    """
    return qualified(expr.func if isinstance(expr, ast.Call) else expr, names)


def skip_mark(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """Which of pytest's skip marks a decorator or `pytestmark` entry is, or `None`.

    That is `pytest.mark.skip`, `pytest.mark.skipif` or `pytest.mark.xfail`, called
    or not, through whatever name the imports give it.
    """
    mark = mark_name(expr, names)
    return mark if mark in _SKIP_MARKS else None


def pytestmark_entries(statement: ast.stmt) -> list[ast.expr]:
    """The marks a `pytestmark = ...` statement applies; none for any other."""
    if not (
        isinstance(statement, ast.Assign)
        and any(
            isinstance(t, ast.Name) and t.id == "pytestmark" for t in statement.targets
        )
    ):
        return []
    value = statement.value
    return list(value.elts) if isinstance(value, ast.List | ast.Tuple) else [value]


def is_always_skipped_by(expr: ast.expr, names: Mapping[str, str]) -> bool:
    """Whether a mark skips whatever the run: `skip`, or `skipif` on a truthy constant.

    A string condition is code pytest evaluates, so it is not a constant here.
    """
    mark = skip_mark(expr, names)
    if mark == SKIP:
        return True
    return (
        mark == SKIPIF
        and isinstance(expr, ast.Call)
        and bool(expr.args)
        and all(
            isinstance(arg, ast.Constant)
            and not isinstance(arg.value, str)
            and bool(arg.value)
            for arg in expr.args
        )
    )


def top_level_skips(body: list[ast.stmt], names: Mapping[str, str]) -> list[ast.Call]:
    """The `pytest.skip(...)` calls that are statements of the body itself.

    One under an `if`, a loop, a `try` or a `with` runs only sometimes, so it isn't
    one of them.
    """
    return [
        statement.value
        for statement in body
        if isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
        and qualified(statement.value.func, names) == SKIP_CALL
    ]


def _pytestmark(body: list[ast.stmt]) -> Iterator[ast.expr]:
    """The marks a module's or class's own `pytestmark` statements apply."""
    for statement in body:
        yield from pytestmark_entries(statement)


def marks_on(test: TestFunction, module: ast.Module) -> Iterator[ast.expr]:
    """Every mark pytest applies to a test, as written.

    Those are its own decorators, its classes' decorators and `pytestmark` entries,
    and the module's `pytestmark`. Each is read through the module's imports
    (`mark_name`, `skip_mark`).
    """
    yield from test.node.decorator_list
    for cls in test.classes:
        yield from cls.decorator_list
        yield from _pytestmark(cls.body)
    yield from _pytestmark(module.body)


def skips_unconditionally(test: TestFunction, module: ast.Module) -> bool:
    """Whether a test skips whatever the run, by a mark or its own body.

    A mark pytest applies to it (`marks_on`) is `pytest.mark.skip` (or `skipif` on
    a truthy constant), or one of its own body's statements, or of the module's, is
    `pytest.skip(...)`.
    """
    names = module_imports(module)
    return (
        any(is_always_skipped_by(mark, names) for mark in marks_on(test, module))
        or bool(top_level_skips(test.node.body, test.imports))
        or bool(top_level_skips(module.body, names))
    )


def scoped_walk(
    module: ast.Module, separator: str
) -> Iterator[tuple[str, ast.AST, Mapping[str, str]]]:
    """Every node of a module with where it is and the imported names it sees.

    Where it is names the innermost function or class around it, with the ones
    around that (`Parser.parse`, or `TestX::test_y` with `::`), or `<module>`. A
    `def` or `class` itself, its decorators included, is where its name is bound;
    what is inside it is in it, and a function's own imports and parameters change
    the names its code sees, as `imports_seen_by` says.
    """

    def visit(
        node: ast.AST, where: str, names: Mapping[str, str]
    ) -> Iterator[tuple[str, ast.AST, Mapping[str, str]]]:
        for child in ast.iter_child_nodes(node):
            yield where, child, names
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                inner = inside(where, child.name, separator)
                inner_names = (
                    names
                    if isinstance(child, ast.ClassDef)
                    else imports_seen_by(child, names)
                )
                for decorator in child.decorator_list:
                    for sub in ast.walk(decorator):
                        yield where, sub, names
                for part in child.body:
                    yield inner, part, inner_names
                    yield from visit(part, inner, inner_names)
            else:
                yield from visit(child, where, names)

    yield from visit(module, MODULE, module_imports(module))
