"""The cheating family (DS4xx): ways to go green without the code working.

Skipping a failing test, or making production code act differently under test,
turns the run green while the behaviour stays broken. DS401 and DS402 read test
files; DS403 is the one check that reads production code.
"""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.ast_tools import (
    SKIP,
    SKIP_CALL,
    TEST_PATH,
    XFAIL,
    XFAIL_CALL,
    calls_to,
    inside,
    is_always_skipped_by,
    module_imports,
    pytestmark_entries,
    qualified,
    scoped_walk,
    skip_mark,
    top_level_skips,
)
from pytest_drill_sergeant.checks.base import Check, Hit, Kind, SourceFile, TestFile
from pytest_drill_sergeant.findings import MODULE, Level

_SKIP_CALLS = frozenset({SKIP_CALL, XFAIL_CALL})

# What production code can ask about the process it runs in: the modules loaded,
# the command line and the environment.
_PROBES = frozenset(
    {"sys.modules", "sys.argv", "os.environ", "os.environb", "os.getenv", "os.getenvb"}
)


def _blank(reason: ast.expr | None) -> bool:
    """Whether a reason says nothing: absent, `None`, or a blank string."""
    if reason is None:
        return True
    return isinstance(reason, ast.Constant) and (
        reason.value is None
        or (isinstance(reason.value, str) and not reason.value.strip())
    )


def _keyword(call: ast.Call, *names: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg in names), None)


def _mark_has_no_reason(mark: str, expr: ast.expr) -> bool:
    """Whether a skip mark gives no reason.

    `skip` takes one by keyword or first by position; `skipif` and `xfail` take
    their conditions by position, so only `reason=` counts.
    """
    if not isinstance(expr, ast.Call):
        return True
    reason = _keyword(expr, "reason")
    if reason is None and mark == SKIP and expr.args:
        reason = expr.args[0]
    return _blank(reason)


def _call_has_no_reason(call: ast.Call) -> bool:
    """Whether `pytest.skip(...)` or `pytest.xfail(...)` gives no reason.

    Either takes one first by position or as `reason=`; `pytest.skip` also by its
    old name, `msg=`.
    """
    reason = _keyword(call, "reason", "msg")
    if reason is None and call.args:
        reason = call.args[0]
    return _blank(reason)


def _marks(module: ast.Module) -> Iterator[tuple[str, ast.expr, Mapping[str, str]]]:
    """Every mark on a function or class, and every `pytestmark` entry.

    Each comes with what it marks (the test, class or `<module>`) and the imported
    names it sees.
    """
    for where, node, names in scoped_walk(module, TEST_PATH):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            marked = inside(where, node.name, TEST_PATH)
            for decorator in node.decorator_list:
                yield marked, decorator, names
        elif isinstance(node, ast.stmt):
            for entry in pytestmark_entries(node):
                yield where, entry, names


def _unconditional_skip_calls(file: TestFile) -> list[tuple[str, ast.Call]]:
    """The `pytest.skip(...)` calls that skip on every run, each with where it is.

    Those are the statements of a test's own body, or of the module's, under no
    condition.
    """
    calls = [
        (test.name, call)
        for test in file.tests
        for call in top_level_skips(test.node.body, test.imports)
    ]
    return calls + [
        (MODULE, call)
        for call in top_level_skips(file.module.body, module_imports(file.module))
    ]


def _find_skip_without_reason(file: TestFile) -> Iterator[Hit]:
    # A skip that happens on every run is left to DS402, reason or not, only where
    # DS402 reports.
    fix = (
        'give it `reason="..."` saying what is wrong and when the test can run '
        "again, such as a ticket link."
    )
    for where, expr, names in _marks(file.module):
        mark = skip_mark(expr, names)
        if mark is not None and _mark_has_no_reason(mark, expr):
            what = "is marked an expected failure" if mark == XFAIL else "is skipped"
            yield Hit.at(
                where,
                expr.lineno,
                found=f"{what} with no reason: `@{ast.unparse(expr)}`.",
                fix=fix,
                left_to=(
                    UNCONDITIONAL_SKIP.code
                    if is_always_skipped_by(expr, names)
                    else None
                ),
            )
    unconditional = {id(call) for _, call in _unconditional_skip_calls(file)}
    for where, node, names in scoped_walk(file.module, TEST_PATH):
        if (
            isinstance(node, ast.Call)
            and calls_to(node, _SKIP_CALLS, names)
            and _call_has_no_reason(node)
        ):
            yield Hit.at(
                where,
                node.lineno,
                found=f"skips with no reason: `{ast.unparse(node)}`.",
                fix=fix,
                left_to=UNCONDITIONAL_SKIP.code if id(node) in unconditional else None,
            )


SKIP_WITHOUT_REASON = Check(
    code="DS401",
    name="skip-without-reason",
    kind=Kind.DEFECT,
    default_level=Level.OFF,
    voice=(
        "You benched a soldier and didn't write down WHY, recruit?",
        "A skip with no reason is a deserter with no paperwork! FILL IT OUT!",
        "Nobody will ever know why this test stopped marching, maggot! WRITE IT DOWN!",
    ),
    why=(
        "A skip or xfail with no reason can't be reviewed or revisited: nobody can "
        "tell a real limitation from a failing test hidden to go green."
    ),
    explain=(
        "Flags `pytest.mark.skip`, `pytest.mark.skipif` and `pytest.mark.xfail` on a "
        "test, a class or the module's `pytestmark`, and calls to `pytest.skip` and "
        "`pytest.xfail`, that give no reason or a blank one. `skip` and the calls "
        "take a reason first by position or as `reason=`; `skipif` and `xfail` only "
        "as `reason=`, since their positional arguments are conditions. A reason in "
        "a variable counts. Import aliases are followed; a local function named "
        "`skip` is not pytest's, and `pytest.importorskip` names its module itself. "
        "Say what is wrong and when the test can run again. A skip on every run "
        "(`pytest.mark.skip`, `skipif` on a truthy constant, `pytest.skip()` "
        "under no condition) is left to DS402 unconditional-skip."
    ),
    bad_example=(
        "import sys\n"
        "\n"
        "import pytest\n"
        "\n"
        "@pytest.mark.skipif(sys.platform == 'win32')\n"
        "def test_path_uses_forward_slashes():\n"
        "    assert invoice_path(7) == 'invoices/7.pdf'\n"
    ),
    good_example=(
        "import sys\n"
        "\n"
        "import pytest\n"
        "\n"
        "@pytest.mark.skipif(sys.platform == 'win32', reason='POSIX paths only, #88')\n"
        "def test_path_uses_forward_slashes():\n"
        "    assert invoice_path(7) == 'invoices/7.pdf'\n"
    ),
    find=_find_skip_without_reason,
)


def _find_unconditional_skip(file: TestFile) -> Iterator[Hit]:
    for where, expr, names in _marks(file.module):
        if is_always_skipped_by(expr, names):
            yield Hit.at(
                where,
                expr.lineno,
                found=f"is skipped on every run: `@{ast.unparse(expr)}`.",
                fix=(
                    "fix what makes it fail and delete the mark; if it can't run "
                    "somewhere, use `pytest.mark.skipif` on that condition, with a "
                    "reason."
                ),
            )
    for where, call in _unconditional_skip_calls(file):
        written = ast.unparse(call)
        yield Hit.at(
            where,
            call.lineno,
            found=f"skips on every run: `{written}` runs under no condition.",
            fix=(
                f"fix what makes it fail and delete `{written}`; if it can't run "
                "somewhere, call it only under that condition (`if ...:`), with a "
                "reason."
            ),
        )


UNCONDITIONAL_SKIP = Check(
    code="DS402",
    name="unconditional-skip",
    kind=Kind.DEFECT,
    default_level=Level.OFF,
    voice=(
        "Skipping the test doesn't fix the code, recruit! It hides the body!",
        "A test that never runs is a soldier who never shows up! GET IT BACK IN LINE!",
        "You silenced the alarm and called the fire OUT? NOT ON MY WATCH!",
    ),
    why=(
        "A test skipped on every run never checks anything again: the run stays "
        "green while the behaviour it covered is broken."
    ),
    explain=(
        "Flags a test skipped on every run: `pytest.mark.skip` on the test, its "
        "class or the module's `pytestmark`, `pytest.mark.skipif` on a truthy "
        "constant (`skipif(True)`), or `pytest.skip(...)` as a statement of the "
        "test's own body, or of the module's, under no `if`, loop, `try` or `with`. "
        "A skip under a condition, `skipif` on a real condition and "
        "`pytest.importorskip` run only sometimes, and are not flagged. Fix what "
        "makes the test fail, or skip it only where it can't run. Such a test is "
        "left to this check, not DS101 no-real-assertion."
    ),
    bad_example=(
        "import pytest\n"
        "\n"
        "@pytest.mark.skip(reason='pre-existing failure')\n"
        "def test_create_record():\n"
        "    assert create_record('ada').id == 1\n"
    ),
    good_example=(
        "def test_create_record():\n    assert create_record('ada').id == 1\n"
    ),
    find=_find_unconditional_skip,
)


def _names_pytest(expr: ast.expr) -> bool:
    """Whether an expression is a string literal naming pytest (`PYTEST_...` too)."""
    return (
        isinstance(expr, ast.Constant)
        and isinstance(expr.value, str)
        and "pytest" in expr.value.lower()
    )


def _probe(expr: ast.expr, names: Mapping[str, str]) -> str | None:
    """What an expression asks the process about, named in full, or `None`.

    An expression asks when it is one of the probes (`sys.modules`, `sys.argv`,
    `os.environ`, `os.getenv`), through the imports, or is built on one: an
    attribute, item or call of it (`sys.argv[0].endswith`, `os.environ.get`).
    """
    while True:
        target = qualified(expr, names)
        if target is not None and any(
            target == probe or target.startswith(f"{probe}.") for probe in _PROBES
        ):
            return target
        if isinstance(expr, ast.Attribute | ast.Subscript):
            expr = expr.value
        elif isinstance(expr, ast.Call):
            expr = expr.func
        else:
            return None


def _asks_about_pytest(node: ast.AST, names: Mapping[str, str]) -> bool:
    """Whether a node asks a probe about pytest.

    That is a comparison of a probe with a literal naming pytest (`"pytest" in
    sys.modules`), an item of a probe looked up by one (`os.environ["PYTEST_..."]`),
    or a call on a probe given one (`os.getenv("PYTEST_CURRENT_TEST")`,
    `sys.argv[0].endswith("pytest")`).
    """
    if isinstance(node, ast.Compare):
        operands = [node.left, *node.comparators]
        return any(_names_pytest(o) for o in operands) and any(
            _probe(o, names) for o in operands
        )
    if isinstance(node, ast.Subscript):
        return _names_pytest(node.slice) and _probe(node.value, names) is not None
    if isinstance(node, ast.Call):
        values = [*node.args, *(k.value for k in node.keywords)]
        return any(_names_pytest(v) for v in values) and (
            _probe(node.func, names) is not None
        )
    return False


def _find_test_special_casing(file: SourceFile) -> Iterator[Hit]:
    reported: set[int] = set()
    for where, node, names in scoped_walk(file.module, "."):
        if not isinstance(node, ast.expr) or node.lineno in reported:
            continue
        if _asks_about_pytest(node, names):
            reported.add(node.lineno)
            yield Hit.at(
                where,
                node.lineno,
                found=f"checks whether tests are running: `{ast.unparse(node)}`.",
                fix=(
                    "delete the check, so the code runs the same under test; let "
                    "the test change what it needs from outside (a parameter, a "
                    "fixture, `monkeypatch`)."
                ),
            )


TEST_SPECIAL_CASING = Check(
    code="DS403",
    name="test-special-casing",
    kind=Kind.DEFECT,
    default_level=Level.OFF,
    voice=(
        "Your code salutes when the inspector walks in and slacks off when he leaves!",
        "Rigging the range so you can't miss is CHEATING, recruit!",
        "Code that knows it's being tested is code that's lying to the tests, maggot!",
    ),
    why=(
        "Production code that checks whether tests are running acts one way under "
        "test and another for real, so the tests pass on behaviour no user gets."
    ),
    explain=(
        "Flags production code that checks whether pytest is running: a comparison, "
        "lookup or call on `sys.modules`, `sys.argv`, `os.environ` or `os.getenv` "
        "with a string naming pytest, such as `'pytest' in sys.modules`, "
        "`os.environ.get('PYTEST_CURRENT_TEST')` or `sys.argv[0].endswith('pytest')`. "
        "Import aliases are followed; a dict of your own that happens to hold "
        "'pytest', or a flag such as `TESTING`, is not flagged, since a name says "
        "nothing about what it holds. It reads the production code in "
        "`drill_sergeant_source_dirs`, or `src/` when that is empty, in full every "
        "run; with neither it is skipped, and the output says so. Delete the check "
        "and let the test change what it needs from outside."
    ),
    bad_example=(
        "import sys\n"
        "\n"
        "def charge(card, amount):\n"
        "    if 'pytest' in sys.modules:\n"
        "        return 'ok'\n"
        "    return gateway.charge(card, amount)\n"
    ),
    good_example=(
        "def charge(card, amount, gateway):\n    return gateway.charge(card, amount)\n"
    ),
    find_in_source=_find_test_special_casing,
)
