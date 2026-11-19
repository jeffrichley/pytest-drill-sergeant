"""The assertions family (DS2xx): assertions that prove nothing.

Every check here reads only `assert` statements, and leaves a truthy constant or a
non-empty tuple (`assert True`) to no-real-assertion. Each `assert` gets one kind,
tautological before mirror before weak, so one assertion is never reported twice.
"""

import ast
import copy
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto

from pytest_drill_sergeant.checks.ast_tools import (
    call_name,
    is_always_true,
    is_real_assertion,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# Comparisons that hold whenever both sides are the same value.
_TRUE_ON_IDENTITY = (ast.Eq, ast.Is, ast.LtE, ast.GtE)

# Builtins whose result is only a truthiness or type fact about their argument.
_WEAK_CALLS = frozenset({"bool", "isinstance", "hasattr", "callable"})

# Name prefixes of functions that answer a yes-or-no question exactly.
_PREDICATE_PREFIXES = ("is_", "has_", "can_", "should_")

# Node types a literal is built from: values, containers and operators, no names.
_LITERAL_NODES = (
    ast.Constant,
    ast.Tuple,
    ast.List,
    ast.Set,
    ast.Dict,
    ast.UnaryOp,
    ast.BinOp,
    ast.expr_context,
    ast.operator,
    ast.unaryop,
)

# Name prefixes that mark a name as the expected value, not a result.
_EXPECTATION_NAMES = ("expect", "want", "exp_")

_FLIPPED: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Lt: ast.Gt,
    ast.Gt: ast.Lt,
    ast.LtE: ast.GtE,
    ast.GtE: ast.LtE,
}


class _Kind(Enum):
    """What one `assert` can prove."""

    IGNORED = auto()  # A truthy constant or tuple: no-real-assertion's to report.
    TAUTOLOGICAL = auto()
    MIRROR = auto()
    WEAK = auto()
    FLAG = auto()  # An attribute or item's truthiness: neither weak nor exact.
    STRONG = auto()


@dataclass(frozen=True)
class _Verdict:
    """One `assert`, its kind, and the words that explain it.

    Attributes:
        node: The `assert` statement.
        kind: What it can prove.
        detail: Why it is tautological, or the call it mirrors.
        subjects: What a weak assertion is about.
    """

    node: ast.Assert
    kind: _Kind
    detail: str = ""
    subjects: tuple[str, ...] = ()


def _is_literal(node: ast.AST) -> bool:
    """Whether an expression is built from values alone, so it never changes."""
    return all(isinstance(n, _LITERAL_NODES) for n in ast.walk(node))


def _has_call(node: ast.AST) -> bool:
    return any(isinstance(n, ast.Call) for n in ast.walk(node))


def _same(left: ast.AST, right: ast.AST) -> bool:
    return ast.dump(left) == ast.dump(right)


def _is_constant(node: ast.AST, *values: object) -> bool:
    return (
        isinstance(node, ast.Constant)
        and type(node.value) is not bool
        and node.value in values
    )


def _is_predicate_call(node: ast.AST) -> bool:
    """Whether the expression calls a predicate (`is_valid(...)`), an exact check."""
    if not isinstance(node, ast.Call):
        return False
    return (call_name(node) or "").startswith(_PREDICATE_PREFIXES)


def _is_constant_none(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def _calls_a_class(node: ast.AST) -> bool:
    """Whether the expression calls a CapWords name: a constructor, by convention."""
    return any(
        isinstance(n, ast.Call) and (call_name(n) or "")[:1].isupper()
        for n in ast.walk(node)
    )


def _names(
    test: TestFunction,
) -> tuple[dict[str, list[ast.Name]], dict[str, list[ast.Name]]]:
    """Every name the test's body binds, and every name it reads."""
    stores: defaultdict[str, list[ast.Name]] = defaultdict(list)
    loads: defaultdict[str, list[ast.Name]] = defaultdict(list)
    for node in walk_test(test):
        if isinstance(node, ast.Name):
            uses = loads if isinstance(node.ctx, ast.Load) else stores
            uses[node.id].append(node)
    return stores, loads


def _is_simple_assignment(name: ast.Name, parent: ast.AST) -> bool:
    """Whether `name` is the one target of a plain `name = value`."""
    if isinstance(parent, ast.Assign):
        return len(parent.targets) == 1 and parent.targets[0] is name
    return isinstance(parent, ast.AnnAssign) and parent.value is not None


def _bindings(test: TestFunction) -> dict[str, ast.Assign | ast.AnnAssign]:
    """The names a test binds once and only reads in assertions, with their bindings.

    Such a name is a stand-in for its value: nothing in the test passes it to code
    that could change it. A name read anywhere else (a call argument, a method
    receiver) is not one, and nor is a name only read to bind one of those.
    """
    parents = {
        child: parent
        for parent in ast.walk(test.node)
        for child in ast.iter_child_nodes(parent)
    }
    stores, loads = _names(test)
    assigns: dict[ast.AST, str] = {}
    for name, nodes in stores.items():
        parent = parents[nodes[0]]
        if len(nodes) == 1 and _is_simple_assignment(nodes[0], parent):
            assigns[parent] = name

    def reader(node: ast.AST) -> str | None:
        """`assert` if the read is in an assertion, else the name it helps bind."""
        while node is not test.node:
            node = parents[node]
            if isinstance(node, ast.Assert):
                return "assert"
            if node in assigns:
                return assigns[node]
        return None

    readers = {
        name: {reader(load) for load in loads[name]} for name in assigns.values()
    }
    alive = set(assigns.values())
    while dropped := {n for n in alive if not readers[n] <= {"assert"} | alive - {n}}:
        alive -= dropped
    return {
        name: statement
        for statement, name in assigns.items()
        if name in alive and isinstance(statement, ast.Assign | ast.AnnAssign)
    }


class _Substitute(ast.NodeTransformer):
    """Replaces each bound name with its value, recursively."""

    def __init__(self, bindings: dict[str, ast.expr]) -> None:
        self.bindings = bindings
        self.active: set[str] = set()

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id not in self.bindings or node.id in self.active:
            return node
        self.active.add(node.id)
        value: ast.AST = self.visit(copy.deepcopy(self.bindings[node.id]))
        self.active.discard(node.id)
        return value


def _resolve(expr: ast.expr, bindings: dict[str, ast.expr]) -> ast.expr:
    """The expression with every bound name replaced by its value."""
    resolved: ast.expr = _Substitute(bindings).visit(copy.deepcopy(expr))
    return resolved


def _multiplies_by_zero(node: ast.AST) -> ast.expr | None:
    """The operand a `* 0` in the expression throws away, if there is one."""
    for n in ast.walk(node):
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mult):
            if _is_constant(n.right, 0) and not _is_literal(n.left):
                return n.left
            if _is_constant(n.left, 0) and not _is_literal(n.right):
                return n.right
    return None


def _tautology(raw: ast.expr, aliased: ast.expr, resolved: ast.expr) -> str | None:
    """Why an assertion can't fail, if it can't.

    `aliased` is `raw` with only names bound to literals or other names replaced;
    `resolved` has every bound name replaced.
    """
    dropped = _multiplies_by_zero(raw) or _multiplies_by_zero(resolved)
    if dropped is not None:
        return f"it multiplies `{ast.unparse(dropped)}` by zero, so its value drops out"
    if not isinstance(aliased, ast.Compare):
        if _is_literal(aliased):
            return "it checks only values the test wrote itself"
        return None
    operands = [aliased.left, *aliased.comparators]
    if all(_is_literal(operand) for operand in operands):
        return "it compares only values the test wrote itself"
    [op] = aliased.ops if len(aliased.ops) == 1 else [None]
    right = aliased.comparators[0]
    if (
        isinstance(op, _TRUE_ON_IDENTITY)
        and _same(aliased.left, right)
        and not _has_call(aliased.left)
    ):
        return f"it compares `{ast.unparse(aliased.left)}` with itself"
    return None


def _is_determinism_check(raw: ast.expr) -> bool:
    """Whether an `==` compares two names, neither named as the expectation.

    `first = f(x); second = f(x); assert first == second` tests that `f` gives the
    same answer every time; `assert result == expected` takes its expectation from
    the code.
    """
    if not isinstance(raw, ast.Compare) or len(raw.comparators) != 1:
        return False
    sides = [raw.left, raw.comparators[0]]
    names = [side.id for side in sides if isinstance(side, ast.Name)]
    return (
        len(names) == 2  # noqa: PLR2004 -- both sides of the `==`
        and names[0] != names[1]
        and not any(name.lower().startswith(_EXPECTATION_NAMES) for name in names)
    )


def _mirrored_call(raw: ast.expr, resolved: ast.expr) -> str | None:
    """The call an `==` puts on both sides, if it does.

    A constructor on both sides (`Point(1, 2) == Point(1, 2)`) is a test of `__eq__`,
    and two results bound to their own names (`first == second`) a test of
    determinism, not a mirror.
    """
    if _is_determinism_check(raw):
        return None
    if not (
        isinstance(resolved, ast.Compare)
        and len(resolved.ops) == 1
        and isinstance(resolved.ops[0], ast.Eq)
    ):
        return None
    left = resolved.left
    if (
        _same(left, resolved.comparators[0])
        and _has_call(left)
        and not _calls_a_class(left)
    ):
        return ast.unparse(left)
    return None


def _normalised(compare: ast.Compare) -> tuple[ast.expr, ast.cmpop, ast.expr]:
    """A one-operator comparison with any lone constant moved to the right."""
    left, op, right = compare.left, compare.ops[0], compare.comparators[0]
    if isinstance(left, ast.Constant) and not isinstance(right, ast.Constant):
        flipped = _FLIPPED.get(type(op), type(op))
        return right, flipped(), left
    return left, op, right


def _is_call_to(node: ast.AST, names: frozenset[str]) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in names
    )


def _weak_subjects(test: ast.expr) -> list[ast.expr] | None:
    """What a weak assertion is about, or `None` if the assertion is not weak.

    Weak means true for almost any value: a bare name's truthiness, `is not None`,
    `isinstance`, `hasattr`, `callable`, `>= 0`, or a length that is merely non-zero.
    An attribute or item's truthiness (`assert worker.done`) is usually a flag the
    code sets, so it is not weak on its own.
    """
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        subjects: list[ast.expr] = []
        for value in test.values:
            found = _weak_subjects(value)
            if found is None:
                return None
            subjects += found
        return subjects
    if isinstance(test, ast.Name):
        return [test]
    if isinstance(test, ast.Call) and _is_call_to(test, _WEAK_CALLS) and test.args:
        return [test.args[0]]
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1):
        return None
    left, op, right = _normalised(test)
    is_len = _is_call_to(left, frozenset({"len"}))
    subject = left.args[0] if is_len and isinstance(left, ast.Call) else left
    weak = (
        (isinstance(op, ast.IsNot | ast.NotEq) and _is_constant_none(right))
        or (
            _is_call_to(left, frozenset({"bool"}))
            and isinstance(op, ast.Is | ast.Eq)
            and isinstance(right, ast.Constant)
            and right.value is True
        )
        or (isinstance(op, ast.GtE) and _is_constant(right, 0))
        or (
            is_len
            and (
                (isinstance(op, ast.Gt | ast.NotEq) and _is_constant(right, 0))
                or (isinstance(op, ast.GtE) and _is_constant(right, 1))
            )
        )
    )
    if weak and isinstance(subject, ast.Call) and _is_call_to(subject, _WEAK_CALLS):
        subject = subject.args[0] if subject.args else subject
    return [subject] if weak else None


def _other_statements(test: TestFunction, known: list[ast.stmt]) -> list[ast.stmt]:
    """The test's statements, at any depth, other than `known` ones.

    Any of them might change what the code under test returns: a call, an
    attribute set, an augmented assignment.
    """
    return [
        node
        for node in walk_test(test)
        if isinstance(node, ast.stmt) and not any(node is k for k in known)
    ]


def _verdicts(test: TestFunction) -> list[_Verdict]:
    """Every `assert` in the test, in source order, with its kind."""
    bindings = _bindings(test)
    values = {name: s.value for name, s in bindings.items() if s.value is not None}
    aliases = {
        name: value
        for name, value in values.items()
        if isinstance(value, ast.Name) or _is_literal(value)
    }
    verdicts = []
    asserts = [node for node in walk_test(test) if isinstance(node, ast.Assert)]
    others = _other_statements(test, [*asserts, *bindings.values()])
    for node in sorted(asserts, key=lambda n: (n.lineno, n.col_offset)):
        test_expr = node.test
        if isinstance(test_expr, ast.Constant) or (
            isinstance(test_expr, ast.Tuple) and test_expr.elts
        ):
            # `assert False` fails the test on purpose, as `pytest.fail` does.
            kind = _Kind.IGNORED if is_always_true(test_expr) else _Kind.STRONG
            verdicts.append(_Verdict(node, kind))
            continue
        # A value read from the code stands in for its name only if nothing else
        # ran between the binding and this assert to change what it reads.
        settled = {
            name: value
            for name, value in values.items()
            if name in aliases
            or not any(
                (bindings[name].end_lineno or 0) < other.lineno < node.lineno
                for other in others
            )
        }
        resolved = _resolve(test_expr, settled)
        why = _tautology(test_expr, _resolve(test_expr, aliases), resolved)
        if why is not None:
            verdicts.append(_Verdict(node, _Kind.TAUTOLOGICAL, why))
            continue
        call = _mirrored_call(test_expr, resolved)
        if call is not None:
            verdicts.append(_Verdict(node, _Kind.MIRROR, call))
            continue
        subjects = _weak_subjects(test_expr)
        if subjects is not None and not _is_predicate_call(resolved):
            names = tuple(f"`{ast.unparse(s)}`" for s in subjects)
            verdicts.append(_Verdict(node, _Kind.WEAK, subjects=names))
            continue
        flag = isinstance(test_expr, ast.Attribute | ast.Subscript)
        verdicts.append(_Verdict(node, _Kind.FLAG if flag else _Kind.STRONG))
    return verdicts


def _has_assertion_call(test: TestFunction) -> bool:
    """Whether the test asserts through something other than an `assert`."""
    return any(
        is_real_assertion(node, test.imports) and not isinstance(node, ast.Assert)
        for node in walk_test(test)
    )


def _and(items: list[str]) -> str:
    """Items as a sentence list: `a`, `a and b`, `a, b and c`."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def _lines(verdicts: list[_Verdict]) -> str:
    numbers = [str(v.node.lineno) for v in verdicts]
    return f"line{'s' if len(numbers) > 1 else ''} {_and(numbers)}"


def _find_weak_assertion(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        verdicts = _verdicts(test)
        weak = [v for v in verdicts if v.kind is _Kind.WEAK]
        if (
            not weak
            or any(v.kind is _Kind.STRONG for v in verdicts)
            or _has_assertion_call(test)
        ):
            continue
        subjects = list(dict.fromkeys(s for v in weak for s in v.subjects))
        yield Hit.on(
            test,
            weak[0].node.lineno,
            found=(
                "makes only weak assertions: each holds for almost any value, "
                "wrong ones included."
            ),
            fix=(
                f"replace the weak assertions on {_lines(weak)} with exact checks: "
                f"assert what {_and(subjects)} should equal, as in "
                "`assert value == expected`."
            ),
        )


def tautological_asserts(test: TestFunction) -> list[ast.Assert]:
    """The test's tautological assertions: the ones tautological-assertion reports.

    Another check that would report the same `assert` leaves it to that one.
    """
    return [v.node for v in _verdicts(test) if v.kind is _Kind.TAUTOLOGICAL]


def _find_tautological_assertion(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for verdict in _verdicts(test):
            if verdict.kind is not _Kind.TAUTOLOGICAL:
                continue
            source = ast.unparse(verdict.node.test)
            yield Hit.on(
                test,
                verdict.node.lineno,
                found=f"has `assert {source}`, which can't fail: {verdict.detail}.",
                fix=(
                    f"replace `assert {source}` with an assertion on what the code "
                    "under test returns, against a value worked out by hand."
                ),
            )


def _find_mirror_assertion(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for verdict in _verdicts(test):
            if verdict.kind is not _Kind.MIRROR:
                continue
            yield Hit.on(
                test,
                verdict.node.lineno,
                found=(
                    f"checks `{verdict.detail}` against itself: both sides of `==` "
                    "make the same call."
                ),
                fix=(
                    f"keep `{verdict.detail}` on one side and put the value it "
                    "should return, worked out by hand, on the other."
                ),
            )


WEAK_ASSERTION = Check(
    code="DS201",
    name="weak-assertion",
    default_level=Level.FAIL,
    voice=(
        "'Is not None'? My GRANDMOTHER is not None, recruit! What IS it?",
        "Truthy, has a length, is a string. You described a potato, maggot!",
        "That assertion passes for the right answer AND every wrong one! PIN IT DOWN!",
    ),
    why=(
        "A weak assertion holds for almost any value, so the test stays green when the "
        "code returns the wrong one."
    ),
    explain=(
        "Flags a test whose only assertions are weak: a bare name's truthiness "
        "(`assert x`, `bool(x) is True`), `is not None`, `isinstance`, `hasattr`, "
        "`callable`, `>= 0`, or a length that is merely non-zero (`len(x) > 0`). One "
        "exact assertion beside them, `pytest.raises` or a mock verification makes the "
        "test fine. An attribute's truthiness (`assert worker.done`) is usually a flag "
        "the code sets: it neither makes a test weak nor excuses weak assertions "
        "beside it. Membership (`x in y`), `> 0` on anything but a length, and a "
        "predicate's result (`ok = is_valid(...)`, then `assert ok`) are left alone. "
        "Assert the exact value the code should produce."
    ),
    bad_example=(
        "def test_apply_discount():\n"
        "    order = apply_discount(make_order(lines=[1000, 1000]), pct=10)\n"
        "    assert order is not None\n"
        "    assert order.total >= 0\n"
    ),
    good_example=(
        "def test_apply_discount_takes_ten_percent_off_total():\n"
        "    order = apply_discount(make_order(lines=[1000, 1000]), pct=10)\n"
        "    assert order.total == 1800\n"
    ),
    find=_find_weak_assertion,
)

TAUTOLOGICAL_ASSERTION = Check(
    code="DS202",
    name="tautological-assertion",
    default_level=Level.FAIL,
    voice=(
        "You asserted that a thing equals itself. Congratulations, you discovered math!",
        "This assertion can't fail, recruit! An alarm that can't ring is a DOORSTOP!",
        "The code under test isn't even IN this assertion! What are you guarding?",
    ),
    why=(
        "A tautological assertion can't fail whatever the code does, so the test "
        "proves nothing while looking like it does."
    ),
    explain=(
        "Flags an `assert` that can't fail: one comparing an expression with itself "
        "(`assert x == x`), one comparing only values the test wrote itself "
        "(`expected = 1; actual = expected; assert actual == expected`, `assert 2 == "
        "2`), or one multiplying the result away (`assert 5 + f(x) * 0 == 5`). A bare "
        "`assert True` is no-real-assertion's to report. Assert on what the code "
        "under test returns, against a value worked out by hand."
    ),
    bad_example=(
        "def test_config_loads():\n"
        '    expected = {"debug": True}\n'
        "    config = expected\n"
        '    load_config("cfg.toml")\n'
        "    assert config == expected\n"
    ),
    good_example=(
        "def test_config_loads_debug_flag(tmp_path):\n"
        '    path = tmp_path / "cfg.toml"\n'
        '    path.write_text("debug = true\\n")\n'
        '    assert load_config(path) == {"debug": True}\n'
    ),
    find=_find_tautological_assertion,
)

MIRROR_ASSERTION = Check(
    code="DS203",
    name="mirror-assertion",
    default_level=Level.FAIL,
    voice=(
        "You checked the code against ITSELF! Of course it agrees, recruit!",
        "Asking the suspect for his own alibi? That's not a test, that's a MIRROR!",
        "Same call on both sides! When it breaks, BOTH sides break, maggot!",
    ),
    why=(
        "A mirror assertion takes its expected value from the code under test, so a "
        "bug changes both sides at once and the test stays green."
    ),
    explain=(
        "Flags an `==` that makes the same call on both sides, directly "
        '(`assert slugify("Hello World") == slugify("Hello World")`) or through names '
        "the test bound to it (`expected = gross_price(100, 20)`) with nothing else "
        "called in between. A constructor on "
        "both sides (`Point(1, 2) == Point(1, 2)`) tests `__eq__` and is fine, and so "
        "is the same function called with different arguments, or two results bound "
        "to their own names, neither named as the expectation (`first == second`), "
        "which tests that the call is deterministic. A formula copied from "
        "the code by hand is not caught. Put the value the call should return, worked "
        "out by hand, on one side."
    ),
    bad_example=(
        "def test_slugify():\n"
        '    assert slugify("Hello World") == slugify("Hello World")\n'
    ),
    good_example=(
        "def test_slugify_lowercases_and_hyphenates():\n"
        '    assert slugify("Hello World") == "hello-world"\n'
    ),
    find=_find_mirror_assertion,
)
