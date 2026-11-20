"""The brittleness family (DS6xx): tests that break when behaviour hasn't changed."""

import ast
from collections.abc import Iterator

from pytest_drill_sergeant.checks.assertions import tautological_asserts
from pytest_drill_sergeant.checks.ast_tools import (
    call_name,
    instance_param,
    is_real_assertion,
    walk_test,
)
from pytest_drill_sergeant.checks.base import Check, Hit, TestFile, TestFunction
from pytest_drill_sergeant.findings import Level

# Calls whose result is rendered text.
_RENDERING_CALLS = frozenset({"str", "repr", "format"})

# Attributes that hold rendered text: exception messages, captured output, log text.
_TEXT_ATTRIBUTES = frozenset(
    {"message", "msg", "out", "err", "text", "output", "stdout", "stderr"}
)

# A literal of at least this many words is prose, not a value.
_PROSE_WORDS = 3


def _asserts(test: TestFunction) -> Iterator[ast.Assert]:
    """The `assert` statements in a test, nested ones included."""
    for node in walk_test(test):
        if isinstance(node, ast.Assert):
            yield node


def _is_rendered_text(node: ast.expr) -> bool:
    """Whether an expression is rendered text.

    That is a `str`, `repr` or `format` call, or a text attribute such as `.message`,
    `.out` or `.output`, through any string methods called on it (`.strip()`).
    """
    while (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr not in _TEXT_ATTRIBUTES
    ):
        node = node.func.value
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id in _RENDERING_CALLS
    return isinstance(node, ast.Attribute) and node.attr in _TEXT_ATTRIBUTES


def _literal_text(node: ast.expr) -> str | None:
    """A string literal's text, with each f-string placeholder standing as one word."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(
            str(part.value) if isinstance(part, ast.Constant) else "x"
            for part in node.values
        )
    return None


def _is_prose(node: ast.expr) -> bool:
    """Whether an expression is a string literal of several words."""
    text = _literal_text(node)
    return text is not None and len(text.split()) >= _PROSE_WORDS


def _brittle_side(compare: ast.Compare) -> ast.expr | None:
    """The rendered text an `==` or `!=` compares with a prose literal, if any."""
    if len(compare.ops) != 1 or not isinstance(compare.ops[0], ast.Eq | ast.NotEq):
        return None
    left, right = compare.left, compare.comparators[0]
    for text, literal in ((left, right), (right, left)):
        if _is_rendered_text(text) and _is_prose(literal):
            return text
    return None


def _find_brittle_string_match(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for assertion in _asserts(test):
            compare = assertion.test
            if not isinstance(compare, ast.Compare):
                continue
            text = _brittle_side(compare)
            if text is None:
                continue
            shown = ast.unparse(text)
            yield Hit.on(
                test,
                assertion.lineno,
                found=f"compares `{shown}` with a whole sentence of expected text.",
                fix=(
                    f"assert that `{shown}` contains the words that matter "
                    '(`"..." in ...`), use `pytest.raises(..., match=...)`, or '
                    "assert on structured data instead of the wording."
                ),
            )


BRITTLE_STRING_MATCH = Check(
    code="DS601",
    name="brittle-string-match",
    default_level=Level.FAIL,
    voice=(
        "Fix one typo in a message and this test goes down! That's not a test, it's "
        "a spell checker!",
        "You memorized the whole sentence, recruit? Check what MATTERS!",
        "Exact prose in an assert! One comma moves and your whole squad is dead!",
    ),
    why=(
        "Comparing rendered text with a whole sentence breaks on any rewording, so "
        "the test fails when behaviour hasn't changed and doesn't say which part of "
        "the text was the contract."
    ),
    explain=(
        "Flags an `assert` that compares rendered text (`str(...)`, `repr(...)`, "
        "`format(...)`, or a `.message`, `.msg`, `.out`, `.err`, `.text`, `.output`, "
        "`.stdout` or `.stderr` attribute) with `==` or `!=` against a string "
        "literal of three or more words. Match the part that matters with `in` or "
        "`pytest.raises(..., match=...)`, or assert on structured data such as the "
        "exception type or parsed fields."
    ),
    bad_example=(
        "import pytest\n"
        "\n"
        "def test_invalid_email():\n"
        "    with pytest.raises(ValueError) as excinfo:\n"
        '        validate("nope")\n'
        "    assert str(excinfo.value) == "
        "\"Invalid email: 'nope' has no @ symbol.\"\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "def test_invalid_email():\n"
        '    with pytest.raises(ValueError, match="@"):\n'
        '        validate("nope")\n'
    ),
    find=_find_brittle_string_match,
)


def _asserted(
    test: TestFunction,
) -> Iterator[tuple[ast.Assert | ast.Call, list[ast.expr]]]:
    """Each real assertion in a test, with the expressions it checks.

    An `assert` checks its test. An asserting call (`self.assertEqual`, a mock's
    `assert_called_once`, a pytest-check helper, a matcher on Playwright's
    `expect(...)`) checks its arguments and the object it is called on.
    """
    for node in walk_test(test):
        if isinstance(node, ast.Assert):
            yield node, [node.test]
        elif isinstance(node, ast.Call) and is_real_assertion(node, test.imports):
            func = node.func
            receiver = [func.value] if isinstance(func, ast.Attribute) else []
            yield node, [*receiver, *node.args]


# Underscored names that are public API: namedtuple's methods and fields.
_PUBLIC_UNDERSCORED = frozenset(
    {"_asdict", "_replace", "_fields", "_field_defaults", "_make"}
)


def _is_private_attribute(node: ast.AST, test: TestFunction) -> bool:
    """Whether a node reads a private attribute of something other than the test.

    Dunders are public protocol, namedtuple's `_asdict` and kin are public API, and
    an attribute of the instance a test in a class takes belongs to the test itself.
    """
    if not isinstance(node, ast.Attribute):
        return False
    name = node.attr
    if not name.startswith("_") or name in _PUBLIC_UNDERSCORED:
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    instance = instance_param(test)
    return not (
        instance is not None
        and isinstance(node.value, ast.Name)
        and node.value.id == instance
    )


def _find_private_state_assertion(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        # An `assert` that can't fail is tautological-assertion's to report.
        tautologies = tautological_asserts(test)
        for assertion, checked in _asserted(test):
            if any(assertion is t for t in tautologies):
                continue
            names = list(
                dict.fromkeys(
                    f"{ast.unparse(node.value)}.{node.attr}"
                    for expression in checked
                    for node in ast.walk(expression)
                    if isinstance(node, ast.Attribute)
                    and _is_private_attribute(node, test)
                )
            )
            if not names:
                continue
            shown = ", ".join(f"`{name}`" for name in names)
            yield Hit.on(
                test,
                assertion.lineno,
                found=f"asserts on private state: {shown}.",
                fix=(
                    f"replace {shown} with the public behaviour it stands for: a "
                    "return value, a public attribute or method, or what a fake "
                    "collaborator received."
                ),
            )


PRIVATE_STATE_ASSERTION = Check(
    code="DS602",
    name="private-state-assertion",
    default_level=Level.FAIL,
    voice=(
        "Who gave you clearance to rifle through PRIVATE quarters, recruit?!",
        "That underscore means KEEP OUT! Test what it does, not what it hides!",
        "Rename one private field and this test dies! A change detector is not a "
        "test, maggot!",
    ),
    why=(
        "An assertion on private state pins how the code works, not what it does, "
        "so a refactor that keeps the behaviour still breaks the test."
    ),
    explain=(
        "Flags an assertion (an `assert`, an `assert*` call such as "
        "`self.assertEqual` or a mock's `assert_called_once`, `pytest.raises` and "
        "kin, a pytest-check helper such as `check.equal`, or a matcher on "
        "Playwright's `expect(...)`) that reads a private "
        "attribute: one starting with `_`, such as `cache._store` or a "
        "name-mangled `obj._Class__x`. Dunders such as `__dict__` or `__name__`, "
        "namedtuple's `_asdict`, `_replace`, `_fields`, `_field_defaults` and "
        "`_make`, and the test's own instance (`self._x`, by whatever name the "
        "instance goes) are exempt, as is private access outside an assertion (injecting a fake in setup) and an `assert` that "
        "can't fail, which tautological-assertion reports. Assert on the public "
        "behaviour instead."
    ),
    bad_example=(
        "def test_cache_miss():\n"
        "    cache = Cache()\n"
        '    cache.get("k")\n'
        "    assert cache._misses == 1\n"
    ),
    good_example=(
        "def test_cache_miss():\n"
        "    cache = Cache()\n"
        '    cache.get("k")\n'
        "    assert cache.stats().misses == 1\n"
    ),
    find=_find_private_state_assertion,
)


# `inspect`'s functions that return source text.
_GETSOURCE = frozenset({"getsource", "getsourcelines"})

# Methods that read a file's text.
_READ_METHODS = frozenset({"read_text", "read_bytes", "read", "readlines", "open"})

# Fixtures whose paths are files the test made, not the project's source.
_TEMP_PATHS = frozenset({"tmp_path", "tmpdir", "tmp_path_factory", "tmpdir_factory"})

# `re` functions that search text.
_RE_SEARCHES = frozenset({"search", "match", "fullmatch", "findall", "finditer"})


def _is_source_path(node: ast.expr) -> bool:
    """Whether a path expression names a project source file.

    That is a `.py` or `.pyi` literal somewhere in it, or a module's `__file__`,
    unless the path is under a temporary directory fixture.
    """
    nodes = list(ast.walk(node))
    if any(isinstance(n, ast.Name) and n.id in _TEMP_PATHS for n in nodes):
        return False
    return any(
        (
            isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and n.value.endswith((".py", ".pyi"))
        )
        or (isinstance(n, ast.Attribute) and n.attr == "__file__")
        for n in nodes
    )


def _is_source_read(call: ast.Call) -> bool:
    """Whether a call reads source text.

    That is `inspect.getsource(...)` or `getsourcelines(...)`, `open(...)` on a
    source file, or a read method such as `.read_text()` on one.
    """
    name = call_name(call)
    if name in _GETSOURCE:
        return True
    if name == "open" and isinstance(call.func, ast.Name):
        return bool(call.args) and _is_source_path(call.args[0])
    return (
        name in _READ_METHODS
        and isinstance(call.func, ast.Attribute)
        and _is_source_path(call.func.value)
    )


def _origin(node: ast.expr, sources: dict[str, str]) -> str | None:
    """Where an expression's source text was read, if it is source text.

    It is when it reads source, names a variable holding source, or calls a method
    on or indexes into source text (`.splitlines()`, `.read()` on an open handle).
    """
    if isinstance(node, ast.Name):
        return sources.get(node.id)
    if isinstance(node, ast.Subscript):
        return _origin(node.value, sources)
    if isinstance(node, ast.Call):
        if _is_source_read(node):
            return ast.unparse(node)
        if isinstance(node.func, ast.Attribute):
            return _origin(node.func.value, sources)
    return None


def _bound_pairs(node: ast.AST) -> Iterator[tuple[ast.expr, ast.expr]]:
    """Each (target, value) a node binds.

    Assignments, `with ... as`, `for` loops and comprehensions bind.
    """
    if isinstance(node, ast.Assign):
        for target in node.targets:
            yield target, node.value
    elif isinstance(node, ast.withitem) and node.optional_vars is not None:
        yield node.optional_vars, node.context_expr
    elif isinstance(node, ast.For | ast.comprehension):
        yield node.target, node.iter


def _source_variables(test: TestFunction) -> dict[str, str]:
    """The test's variables that hold source text, each with where it was read."""
    sources: dict[str, str] = {}
    changed = True
    while changed:
        changed = False
        for node in walk_test(test):
            for target, value in _bound_pairs(node):
                origin = _origin(value, sources)
                if origin is None:
                    continue
                for name in ast.walk(target):
                    if isinstance(name, ast.Name) and name.id not in sources:
                        sources[name.id] = origin
                        changed = True
    return sources


def _grepped(assertion: ast.Assert, sources: dict[str, str]) -> str | None:
    """Where the source text an `assert` searches with `in` or `re` was read."""
    for node in ast.walk(assertion.test):
        searched: list[ast.expr] = []
        if isinstance(node, ast.Compare):
            searched = [
                right
                for op, right in zip(node.ops, node.comparators, strict=True)
                if isinstance(op, ast.In | ast.NotIn)
            ]
        elif isinstance(node, ast.Call) and call_name(node) in _RE_SEARCHES:
            searched = list(node.args)
        for expression in searched:
            origin = _origin(expression, sources)
            if origin is not None:
                return origin
    return None


def _find_source_text_grep(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        sources = _source_variables(test)
        for assertion in _asserts(test):
            origin = _grepped(assertion, sources)
            if origin is None:
                continue
            yield Hit.on(
                test,
                assertion.lineno,
                found=(
                    f"searches source text read by `{origin}` instead of running "
                    "the code."
                ),
                fix=(
                    f"drop `{origin}` and call the code it reads: assert on what it "
                    "returns or does."
                ),
            )


SOURCE_TEXT_GREP = Check(
    code="DS603",
    name="source-text-grep",
    default_level=Level.FAIL,
    voice=(
        "You READ the code instead of RUNNING it? That's a book report, recruit!",
        "Grepping the source proves the words are there, not that they WORK!",
        "Move one line and this test fails; break the logic and it passes! "
        "DISGRACEFUL!",
    ),
    why=(
        "A test that searches source text proves the text is there, not that the "
        "code behaves: it breaks on harmless rewrites and passes when the code is "
        "wrong."
    ),
    explain=(
        "Flags an `assert` that searches source text with `in`, `not in` or a `re` "
        "search (`re.search`, `re.match`, `re.fullmatch`, `re.findall`, "
        "`re.finditer`). Source text is what `inspect.getsource` or "
        "`inspect.getsourcelines` returns, or what is read from a `.py` or `.pyi` "
        "file or a module's `__file__` with `open`, `.read_text()` and the like, "
        "along with the variables holding it. Files under `tmp_path` or `tmpdir` "
        "are exempt, and so is source passed to the code under test. Run the code "
        "and assert on what it does."
    ),
    bad_example=(
        "def test_retry_enabled():\n"
        '    assert "retry=True" in Path("src/client.py").read_text()\n'
    ),
    good_example=(
        "def test_client_retries_once(flaky_server):\n"
        "    Client(flaky_server.url).get()\n"
        "    assert flaky_server.requests == 2\n"
    ),
    find=_find_source_text_grep,
)
