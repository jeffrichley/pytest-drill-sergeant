"""One finding per problem, through the engine: when two checks report the same
problem, the more specific one wins, and only while it is enabled."""

from pathlib import Path

import pytest

from pytest_drill_sergeant.config import resolve
from pytest_drill_sergeant.engine import analyze

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("raw", "codes"),
    [
        ({"drill_sergeant_levels": "DS501=fail"}, {("DS502", 11)}),
        ({"drill_sergeant_levels": ["DS501=fail", "DS502=off"]}, {("DS501", 12)}),
        (
            {
                "drill_sergeant_levels": "DS501=fail",
                "drill_sergeant_per_file_ignores": "*.py: DS502",
            },
            {("DS501", 12)},
        ),
    ],
    ids=["both-on", "near-duplicates-off", "near-duplicates-ignored"],
)
def test_copy_paste_setup_folds_near_duplicates_only_while_they_are_reported(
    raw, codes
):
    corpus = Path(__file__).parent / "corpus" / "near-duplicate-tests"
    config = resolve(raw, corpus)

    findings = analyze([corpus / "test_bad_with_pasted_setup.py"], config)

    assert {(f.code, f.line) for f in findings} == codes


@pytest.mark.parametrize(
    ("raw", "codes"),
    [
        ({"drill_sergeant_levels": ["DS101=fail", "DS702=fail"]}, {("DS702", 18)}),
        ({"drill_sergeant_levels": ["DS101=fail", "DS702=off"]}, {("DS101", 15)}),
        (
            {
                "drill_sergeant_levels": ["DS101=fail", "DS702=fail"],
                "drill_sergeant_per_file_ignores": "*.py: DS702",
            },
            {("DS101", 15)},
        ),
    ],
    ids=["both-on", "swallowed-exception-off", "swallowed-exception-ignored"],
)
def test_no_real_assertion_yields_to_a_swallowed_exception_only_while_it_is_reported(
    raw, codes
):
    corpus = Path(__file__).parent / "corpus" / "swallowed-exception"
    config = resolve(raw, corpus)

    findings = analyze([corpus / "test_bad_make_it_not_crash.py"], config)

    assert {(f.code, f.line) for f in findings if f.test == "test_sync"} == codes


@pytest.mark.parametrize(
    ("source", "on", "codes"),
    [
        (
            "@pytest.mark.skip\ndef test_sync():\n    sync()\n",
            ["DS101=fail", "DS402=fail"],
            {("DS402", 3)},
        ),
        (
            "@pytest.mark.skip\ndef test_sync():\n    sync()\n",
            ["DS101=fail"],
            {("DS101", 4)},
        ),
        (
            "pytestmark = pytest.mark.skip\n\ndef test_sync():\n    sync()\n",
            ["DS101=fail"],
            {("DS101", 5)},
        ),
        (
            "@pytest.mark.skip\ndef test_sync():\n    assert sync() == 1\n",
            ["DS401=fail", "DS402=fail"],
            {("DS402", 3)},
        ),
        (
            "@pytest.mark.skip\ndef test_sync():\n    assert sync() == 1\n",
            ["DS401=fail"],
            {("DS401", 3)},
        ),
        (
            "def test_sync():\n    pytest.skip()\n    assert sync() == 1\n",
            ["DS401=fail", "DS402=fail"],
            {("DS402", 4)},
        ),
        (
            "def test_sync():\n    pytest.skip()\n    assert sync() == 1\n",
            ["DS401=fail"],
            {("DS401", 4)},
        ),
        (
            "@pytest.mark.skipif()\ndef test_sync():\n    assert sync() == 1\n",
            ["DS401=fail", "DS402=fail"],
            {("DS402", 3)},
        ),
        (
            "@pytest.mark.skipif()\ndef test_sync():\n    assert sync() == 1\n",
            ["DS401=fail"],
            {("DS401", 3)},
        ),
    ],
    ids=[
        "no-assertion-both-on",
        "no-assertion-unconditional-skip-off",
        "module-skip-unconditional-skip-off",
        "no-reason-both-on",
        "no-reason-unconditional-skip-off",
        "skip-call-no-reason-both-on",
        "skip-call-no-reason-unconditional-skip-off",
        "skipif-no-condition-both-on",
        "skipif-no-condition-unconditional-skip-off",
    ],
)
def test_check_leaves_an_always_skipped_test_to_ds402_only_while_it_is_reported(
    write_test_file, source, on, codes
):
    """DS402 is the more specific finding for a test that never runs."""
    path = write_test_file("import pytest\n\n" + source)

    findings = analyze([path], resolve({"drill_sergeant_levels": on}))

    assert {(f.code, f.line) for f in findings} == codes
