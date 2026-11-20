"""The marker family (DS9xx): tests a run can't select or skip by category.

A test's marks are its own decorators, its classes' decorators and `pytestmark`
entries, and the module's `pytestmark`, as pytest applies them; each is read through
the imports, so a mark is `pytest.mark.<name>` however it is spelled. Marks a
conftest hook adds at collection time are not in the file, so this check can't see
them.
"""

from collections.abc import Iterator, Mapping

from pytest_drill_sergeant.checks.ast_tools import (
    mark_name,
    marks_on,
    module_imports,
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


def _is_marked(test: TestFunction, file: TestFile, names: Mapping[str, str]) -> bool:
    wanted = {f"{_MARK}{marker}" for marker in file.category_markers}
    return any(mark_name(m, names) in wanted for m in marks_on(test, file.module))


def _fix(file: TestFile) -> str:
    """How to mark a test: the marker its nearest category directory names, or any."""
    by_name = {m.lower(): m for m in file.category_markers}
    nearest = next(
        (d for d in reversed(file.directories) if d.lower() in by_name), None
    )
    if nearest is not None:
        named = by_name[nearest.lower()]
        return (
            f"add `@pytest.mark.{named}`, the category marker its directory "
            f"`{nearest}/` names, or mark the whole module with "
            f"`pytestmark = pytest.mark.{named}`."
        )
    if len(file.category_markers) == 1:
        what = f"`@pytest.mark.{file.category_markers[0]}`"
    else:
        allowed = and_list([f"`@pytest.mark.{m}`" for m in file.category_markers])
        what = f"one of the category markers {allowed}"
    return f"add {what} to the test, its class or the module's `pytestmark`."


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
    default_level=Level.OFF,
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
        "directory, is named for, in any case (`tests/Integration/` suggests "
        "`@pytest.mark.integration`), else lists the configured markers. Marks a "
        "conftest hook adds at collection time are invisible to this static "
        "check. Off by default, a convention a project opts into; turn it on with "
        "`drill_sergeant_levels` (`DS901=fail`). With no category markers "
        "configured, it flags nothing."
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
