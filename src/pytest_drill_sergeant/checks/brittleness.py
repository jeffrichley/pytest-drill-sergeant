"""The brittleness family (DS6xx): tests that break when behaviour hasn't changed."""

import ast
from collections.abc import Iterator

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
    for statement in test.node.body:
        for node in ast.walk(statement):
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
            yield Hit(
                line=assertion.lineno,
                test=test.name,
                found=(
                    f"`{test.name}` compares `{shown}` with a whole sentence of "
                    "expected text."
                ),
                fix=(
                    f"In `{test.name}`, assert that `{shown}` contains the words that "
                    'matter (`"..." in ...`), use `pytest.raises(..., match=...)`, or '
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
        "def test_invalid_email():\n"
        "    with pytest.raises(ValueError) as excinfo:\n"
        '        validate("nope")\n'
        "    assert str(excinfo.value) == "
        "\"Invalid email: 'nope' has no @ symbol.\"\n"
    ),
    good_example=(
        "def test_invalid_email():\n"
        '    with pytest.raises(ValueError, match="@"):\n'
        '        validate("nope")\n'
    ),
    find=_find_brittle_string_match,
)
