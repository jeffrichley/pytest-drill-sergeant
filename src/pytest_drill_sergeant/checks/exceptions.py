"""The exceptions family (DS7xx): how a test expects, or hides, an exception."""

import ast
from collections.abc import Iterator

from pytest_drill_sergeant.checks.base import Check, Hit, TestFile
from pytest_drill_sergeant.findings import Level

# The exception types that every error is an instance of.
_BROAD = frozenset({"Exception", "BaseException"})


def _is_pytest_raises(func: ast.expr) -> bool:
    """Whether a call target is `pytest.raises`, called as such or by its bare name."""
    if isinstance(func, ast.Attribute):
        return (
            isinstance(func.value, ast.Name)
            and func.value.id == "pytest"
            and func.attr == "raises"
        )
    return isinstance(func, ast.Name) and func.id == "raises"


def _expected_exception(call: ast.Call) -> ast.expr | None:
    """The exception type a `pytest.raises` call expects, if it names one."""
    if call.args:
        return call.args[0]
    return next((k.value for k in call.keywords if k.arg == "expected_exception"), None)


def _broad_name(expected: ast.expr | None) -> str | None:
    """The broad type an expected exception names, alone or in a tuple."""
    candidates = expected.elts if isinstance(expected, ast.Tuple) else [expected]
    return next(
        (c.id for c in candidates if isinstance(c, ast.Name) and c.id in _BROAD),
        None,
    )


def _has_match(call: ast.Call) -> bool:
    """Whether a `pytest.raises` call passes a `match=` that isn't `None`."""
    return any(
        k.arg == "match"
        and not (isinstance(k.value, ast.Constant) and k.value.value is None)
        for k in call.keywords
    )


def _find_broad_raises(file: TestFile) -> Iterator[Hit]:
    for test in file.tests:
        for statement in test.node.body:
            for node in ast.walk(statement):
                if not (isinstance(node, ast.Call) and _is_pytest_raises(node.func)):
                    continue
                broad = _broad_name(_expected_exception(node))
                if broad is None or _has_match(node):
                    continue
                yield Hit(
                    line=node.lineno,
                    test=test.name,
                    found=(
                        f"`{test.name}` expects `{broad}` with no `match=` on line "
                        f"{node.lineno}, so any error at all passes it."
                    ),
                    fix=(
                        f"On line {node.lineno} of `{test.name}`, replace `{broad}` "
                        "with the specific exception the code raises, and add "
                        "`match=` for the part of its message that matters."
                    ),
                )


BROAD_RAISES = Check(
    code="DS701",
    name="broad-raises",
    default_level=Level.FAIL,
    voice=(
        "Expecting `Exception`? That's not a target, recruit, that's the whole range!",
        "A typo in your own test raises too, maggot! NAME THE EXCEPTION!",
        "Any error passes this test! Even the wrong one! ESPECIALLY the wrong one!",
    ),
    why=(
        "`pytest.raises(Exception)` with no `match=` passes for any error, including "
        "a `TypeError` from a typo in the test, so it can't tell the expected failure "
        "from a broken one."
    ),
    explain=(
        "Flags `pytest.raises` expecting `Exception` or `BaseException`, alone or in "
        "a tuple, with no `match=`. Name the specific exception the code raises, and "
        "add `match=` for the part of its message that matters."
    ),
    bad_example=(
        "import pytest\n"
        "\n"
        "def test_bad_input():\n"
        "    with pytest.raises(Exception):\n"
        "        parse(None)\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "def test_none_input_rejected():\n"
        '    with pytest.raises(ParseError, match="must not be None"):\n'
        "        parse(None)\n"
    ),
    find=_find_broad_raises,
)
