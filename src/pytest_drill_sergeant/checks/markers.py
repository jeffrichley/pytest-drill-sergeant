"""The marker family (DS9xx): tests a run can't select or skip by category.

A test's marks are its own decorators, its classes' decorators and `pytestmark`
entries, and the module's `pytestmark`, as pytest applies them; each is read through
the imports, so a mark is `pytest.mark.<name>` however it is spelled. Marks a
conftest hook adds at collection time are not in the file, so this check can't see
them.
"""

import ast
from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.ast_tools import (
    mark_name,
    module_imports,
    pytestmark_entries,
)
from pytest_drill_sergeant.checks.base import (
    Check,
    Hit,
    TestFile,
    TestFunction,
    and_list,
)
from pytest_drill_sergeant.findings import Level

# What pytest calls a mark of the given name.
_MARK = "pytest.mark."


def _pytestmark(body: list[ast.stmt]) -> Iterator[ast.expr]:
    """The marks a module's or class's own `pytestmark` statements apply."""
    for statement in body:
        yield from pytestmark_entries(statement)


def _marks_on(test: TestFunction, module: ast.Module) -> Iterator[ast.expr]:
    """Every mark pytest applies to a test: its own, its classes' and the module's."""
    yield from test.node.decorator_list
    for cls in test.classes:
        yield from cls.decorator_list
        yield from _pytestmark(cls.body)
    yield from _pytestmark(module.body)


def _is_marked(test: TestFunction, file: TestFile, names: Mapping[str, str]) -> bool:
    wanted = {f"{_MARK}{marker}" for marker in file.category_markers}
    return any(mark_name(m, names) in wanted for m in _marks_on(test, file.module))


def _fix(file: TestFile) -> str:
    """How to mark a test: the marker its nearest category directory names, or any."""
    named = next(
        (d for d in reversed(file.directories) if d in file.category_markers), None
    )
    if named is not None:
        return (
            f"add `@pytest.mark.{named}`, the category marker its directory "
            f"`{named}/` names, or mark the whole module with "
            f"`pytestmark = pytest.mark.{named}`."
        )
    allowed = and_list([f"`@pytest.mark.{m}`" for m in file.category_markers])
    return (
        f"add one of the category markers {allowed} to the test, its class or the "
        "module's `pytestmark`."
    )


def _find_missing_category_marker(file: TestFile) -> Iterator[Hit]:
    if not file.category_markers:
        return
    names = module_imports(file.module)
    for test in file.tests:
        if not _is_marked(test, file, names):
            yield Hit.on(
                test,
                test.node.lineno,
                found="carries no category marker.",
                fix=_fix(file),
            )


MISSING_CATEGORY_MARKER = Check(
    code="DS901",
    name="missing-category-marker",
    default_level=Level.FAIL,
    voice=(
        "Which unit are you with, recruit? NO MARKINGS, NO DEPLOYMENT!",
        "A soldier without insignia is a soldier nobody can find! MARK IT!",
        "I can't call your squad if you never told me its NAME, maggot!",
    ),
    why=(
        "A test with no category marker can't be selected or skipped with its "
        "category (`pytest -m unit`), so it runs where it doesn't belong or is "
        "left out where it does."
    ),
    explain=(
        "Flags a test that carries none of the configured category markers "
        "(`drill_sergeant_category_markers`, by default `unit integration e2e`): "
        "a `pytest.mark.<marker>` on the test, on its class or a class around it, "
        "in a class's `pytestmark` or in the module's `pytestmark` (one mark or a "
        "list) satisfies it. Other markers don't count. Marks are read through the "
        "imports, so `from pytest import mark` counts; a mark held in a variable "
        "of your own is not followed. The fix suggests the marker that the "
        "nearest directory in the file's path, relative to the config file's "
        "directory, is named for (`tests/integration/` suggests "
        "`@pytest.mark.integration`), else lists the configured markers. Marks a "
        "conftest hook adds at collection time are invisible to this static "
        "check; such projects turn it off. With no category markers configured, "
        "it flags nothing."
    ),
    bad_example=(
        "def test_order_total_adds_line_items():\n    assert order_total([2, 3]) == 5\n"
    ),
    good_example=(
        "import pytest\n"
        "\n"
        "pytestmark = pytest.mark.unit\n"
        "\n"
        "def test_order_total_adds_line_items():\n"
        "    assert order_total([2, 3]) == 5\n"
    ),
    find=_find_missing_category_marker,
)
