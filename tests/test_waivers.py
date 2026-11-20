"""Inline waivers, through the engine: which findings they silence, and with what.

The malformed-waiver check (DS001) is proven through the corpus; this file covers
how waivers apply to findings, and the `drill_sergeant_inline_waivers` switch.
"""

import pytest

from pytest_drill_sergeant.config import resolve
from pytest_drill_sergeant.engine import inspect

pytestmark = pytest.mark.unit

# The checks these waivers name, on: each is off by default until it is proven.
WAIVED_CHECKS_ON = ["DS101=fail", "DS201=fail", "DS403=fail"]
ON = resolve({"drill_sergeant_levels": WAIVED_CHECKS_ON})

# A test with no real assertion (DS101 on line 1), waived on its `def` line.
WAIVED_ON_DEF = "def test_it():  # drill: waive DS101 -- smoke test\n    run()\n"


def flagged(findings):
    return [(f.code, f.line) for f in findings]


def test_waiver_on_the_def_line_waives_the_finding_with_its_reason(write_test_file):
    path = write_test_file(WAIVED_ON_DEF)

    result = inspect([path], ON)

    assert result.findings == []
    assert [(w.finding.code, w.finding.line, w.reason) for w in result.waived] == [
        ("DS101", 1, "smoke test")
    ]


def test_waiver_on_the_flagged_line_waives_the_finding(write_test_file):
    path = write_test_file(
        "def test_it():\n"
        "    value = make()\n"
        "    assert value is not None  # drill: waive DS201 -- any value will do\n"
    )

    result = inspect([path], ON)

    assert result.findings == []
    assert [(w.finding.code, w.finding.line, w.reason) for w in result.waived] == [
        ("DS201", 3, "any value will do")
    ]


@pytest.mark.parametrize(
    ("source", "line"),
    [
        (
            "def test_it():  # drill: waive DS201 -- any value will do\n"
            "    value = make()\n"
            "    assert value is not None\n",
            3,
        ),
        (
            "def test_it(\n"
            "    tmp_path,\n"
            "):  # drill: waive DS201 -- any value will do\n"
            "    value = make(tmp_path)\n"
            "    assert value is not None\n",
            5,
        ),
    ],
    ids=["on-the-def-line", "on-a-wrapped-signatures-closing-line"],
)
def test_def_line_waiver_covers_a_finding_anywhere_in_its_test(
    write_test_file, source, line
):
    path = write_test_file(source)

    result = inspect([path], ON)

    assert flagged(result.findings) == []
    assert flagged(w.finding for w in result.waived) == [("DS201", line)]


def test_def_line_waiver_leaves_other_tests_findings_standing(write_test_file):
    path = write_test_file(
        "def test_one():  # drill: waive DS101 -- smoke test\n"
        "    run()\n"
        "def test_two():\n"
        "    stop()\n"
    )

    result = inspect([path], ON)

    assert flagged(result.findings) == [("DS101", 3)]


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ("def test_it():\n    run()  # drill: waive DS101 -- smoke test\n", 1),
        ("def test_it():\n    # drill: waive DS101 -- smoke test\n    run()\n", 1),
        (
            "@pytest.mark.slow  # drill: waive DS101 -- smoke test\ndef test_it():\n    run()\n",
            2,
        ),
    ],
    ids=["on-another-line", "on-its-own-line", "on-a-decorator-line"],
)
def test_waiver_off_the_def_and_flagged_lines_waives_nothing(
    write_test_file, source, line
):
    path = write_test_file(source)

    result = inspect([path], ON)

    assert (flagged(result.findings), result.waived) == ([("DS101", line)], [])


@pytest.mark.parametrize(
    ("source", "standing"),
    [
        (
            "def test_it():  # drill: waive DS201 -- smoke test\n    run()\n",
            [("DS101", 1)],
        ),
        (
            'def test_it():\n    run("# drill: waive DS101 -- smoke test")\n',
            [("DS101", 1)],
        ),
        (
            "def test_it():  # drill: waive DS001 -- let me off\n"
            "    run()  # drill: waive DS101\n"
            "    assert sorted([2, 1]) == [1, 2]\n",
            [("DS001", 2)],
        ),
    ],
    ids=[
        "for-another-check",
        "text-in-a-string-is-not-a-waiver",
        "malformed-waiver-finding-is-never-waived",
    ],
)
def test_waiver_that_does_not_apply_waives_nothing(write_test_file, source, standing):
    path = write_test_file(source)

    result = inspect([path], ON)

    assert (flagged(result.findings), result.waived) == (standing, [])


@pytest.mark.parametrize(
    "comment",
    [
        "# drill: waive",
        "# drill: waive DS101",
        "# drill: waive DS101 --",
        "# drill: waive -- smoke test",
    ],
    ids=["no-code-or-reason", "no-reason", "empty-reason", "no-code"],
)
def test_malformed_waiver_waives_nothing_and_is_reported(write_test_file, comment):
    path = write_test_file(f"def test_it():  {comment}\n    run()\n")

    result = inspect([path], ON)

    assert (flagged(result.findings), result.waived) == (
        [("DS001", 1), ("DS101", 1)],
        [],
    )


def test_waiver_that_matches_no_finding_is_not_reported(write_test_file):
    path = write_test_file(
        "def test_it():  # drill: waive DS201 -- not needed\n"
        "    assert sorted([2, 1]) == [1, 2]\n"
    )

    result = inspect([path], ON)

    assert (result.findings, result.waived) == ([], [])


def test_waived_finding_keeps_its_level(write_test_file):
    path = write_test_file(WAIVED_ON_DEF)

    result = inspect(
        [path],
        resolve(
            {"drill_sergeant_mode": "warn", "drill_sergeant_levels": WAIVED_CHECKS_ON}
        ),
    )

    assert [w.finding.level for w in result.waived] == ["warn"]


def test_with_inline_waivers_off_waived_findings_stand(write_test_file):
    path = write_test_file(WAIVED_ON_DEF)

    result = inspect(
        [path],
        resolve(
            {
                "drill_sergeant_inline_waivers": "false",
                "drill_sergeant_levels": WAIVED_CHECKS_ON,
            }
        ),
    )

    assert (flagged(result.findings), result.waived) == ([("DS101", 1)], [])


def test_with_inline_waivers_off_malformed_waivers_are_not_reported(write_test_file):
    path = write_test_file(
        "def test_it():  # drill: waive\n    assert sorted([2, 1]) == [1, 2]\n"
    )

    result = inspect(
        [path],
        resolve(
            {
                "drill_sergeant_inline_waivers": "false",
                "drill_sergeant_levels": WAIVED_CHECKS_ON,
            }
        ),
    )

    assert (result.findings, result.waived) == ([], [])


def test_waiver_on_the_flagged_line_of_production_code_waives_the_finding(tmp_path):
    path = tmp_path / "app.py"
    path.write_text(
        "import sys\n"
        "QUIET = 'pytest' in sys.modules  # drill: waive DS403 -- quiet test logs\n"
    )

    result = inspect([], ON, sources=[path])

    assert result.findings == []
    assert [(w.finding.code, w.finding.line) for w in result.waived] == [("DS403", 2)]
