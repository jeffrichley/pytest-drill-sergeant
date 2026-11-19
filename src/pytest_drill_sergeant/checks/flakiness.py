"""The flakiness family (DS8xx): tests whose outcome rides on time or chance."""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# The event-loop sleeps, which yield without waiting when given a zero delay.
_ASYNC_SLEEPS = frozenset({"asyncio.sleep", "trio.sleep", "anyio.sleep"})


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

    Imports under a top-level `if`, `try` or `with` count; a later `def`, `class` or
    assignment of the same name wins, as it does at run time.
    """
    names: dict[str, str] = {}
    pending: list[ast.stmt] = list(module.body)
    while pending:
        statement = pending.pop(0)
        if isinstance(statement, ast.Import | ast.ImportFrom):
            _bind_imports(statement, names)
        elif isinstance(statement, ast.If | ast.Try | ast.With):
            nested = [
                child
                for child in ast.iter_child_nodes(statement)
                if isinstance(child, ast.stmt)
            ]
            nested.extend(
                s
                for handler in getattr(statement, "handlers", [])
                for s in handler.body
            )
            pending[:0] = nested
        else:
            for bound in _bound_names(statement):
                names.pop(bound, None)
    return names


def _bound_names(statement: ast.stmt) -> Iterator[str]:
    """The names a non-import statement binds where it stands."""
    if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        yield statement.name
        return
    targets: list[ast.expr] = []
    if isinstance(statement, ast.Assign):
        targets = statement.targets
    elif isinstance(statement, ast.AnnAssign | ast.AugAssign):
        targets = [statement.target]
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


def _calls(file: TestFile) -> Iterator[tuple[TestFunction, ast.Call, str]]:
    """Every call in every test whose target an import reaches, with its full name."""
    module_names = _module_names(file.module)
    for test in file.tests:
        names = _test_names(test, module_names)
        calls = [node for node in ast.walk(test.node) if isinstance(node, ast.Call)]
        for call in sorted(calls, key=lambda c: (c.lineno, c.col_offset)):
            target = _qualified(call.func, names)
            if target:
                yield test, call, target


def _is_zero(call: ast.Call) -> bool:
    """Whether a call's first argument is the literal zero."""
    return (
        bool(call.args)
        and isinstance(call.args[0], ast.Constant)
        and call.args[0].value == 0
    )


def _find_sleep_in_test(file: TestFile) -> Iterator[Hit]:
    for test, call, target in _calls(file):
        if target != "time.sleep" and (target not in _ASYNC_SLEEPS or _is_zero(call)):
            continue
        written = ast.unparse(call)
        yield Hit(
            line=call.lineno,
            test=test.name,
            found=f"`{test.name}` sleeps for real time: `{written}`.",
            fix=(
                f"In `{test.name}`, replace `{written}` on line {call.lineno} with "
                "a fake or frozen clock, or wait on the condition itself (an event, "
                "a join, a poll with a timeout)."
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
