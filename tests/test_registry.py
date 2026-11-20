"""Every check in the registry carries what it needs to report and teach."""

import re
from pathlib import Path

import pytest

from pytest_drill_sergeant.checks import CHECKS
from pytest_drill_sergeant.checks.markers import MISSING_CATEGORY_MARKER
from pytest_drill_sergeant.engine import Config, analyze
from pytest_drill_sergeant.findings import Level

pytestmark = pytest.mark.unit

CORPUS = Path(__file__).parent / "corpus"


def analyze_as_read_by(check, path):
    """The findings for a file, handed to the engine as the check reads it: as
    production code or as a test file, with the check on even when it is off by
    default.

    An example shows one failure mode, so only the category-marker check's own
    examples are read with that check on: a category marker belongs to the project's
    file, not to an example of another check."""
    config = Config(
        levels={MISSING_CATEGORY_MARKER.code: Level.OFF, check.code: Level.FAIL}
    )
    if check.find_in_source:
        return analyze([], config, sources=[path])
    return analyze([path], config)


def corpus_folder(check):
    """Where a check's corpus files are, and the prefix of their names: production
    code under `source/`, named `bad_*` and `good_*`, or test files `test_bad_*` and
    `test_good_*`."""
    if check.find_in_source:
        return CORPUS / check.name / "source", ""
    return CORPUS / check.name, "test_"


def test_codes_and_names_are_unique():
    assert len({c.code for c in CHECKS}) == len({c.name for c in CHECKS}) == len(CHECKS)


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_check_has_code_name_voice_and_explain_text(check):
    assert re.fullmatch(r"DS\d{3}", check.code)
    assert re.fullmatch(r"[a-z]+(-[a-z]+)*", check.name)
    assert 2 <= len(check.voice) <= 5
    assert all(line.strip() for line in check.voice)
    assert check.why.strip()
    assert check.explain.strip()


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_bad_example_is_flagged_and_good_example_is_clean(check, tmp_path):
    bad = tmp_path / "test_bad.py"
    bad.write_text(check.bad_example)
    good = tmp_path / "test_good.py"
    good.write_text(check.good_example)

    assert check.code in {f.code for f in analyze_as_read_by(check, bad)}
    assert analyze_as_read_by(check, good) == []


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_check_has_at_least_three_bad_and_three_good_corpus_files(check):
    folder, prefix = corpus_folder(check)

    assert len(list(folder.glob(f"{prefix}bad_*.py"))) >= 3
    assert len(list(folder.glob(f"{prefix}good_*.py"))) >= 3


# Proven: zero false positives in a hand-judged sample of real suites (#171).
ON_BY_DEFAULT = {"DS001", "DS106", "DS301", "DS502", "DS603", "DS802", "DS803"}


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_check_reports_by_default_only_once_proven(check):
    """Under the default config a check reports its own bad corpus files only once it
    is proven; every other check is off until a project turns it on."""
    folder, prefix = corpus_folder(check)
    bad = sorted(folder.glob(f"{prefix}bad_*.py"))
    if check.find_in_source:
        findings = analyze([], Config(), sources=bad)
    else:
        findings = analyze(bad, Config())

    assert (check.code in {f.code for f in findings}) == (check.code in ON_BY_DEFAULT)
