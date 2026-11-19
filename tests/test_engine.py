"""The engine seam beyond the corpus: what the config changes."""

from pytest_drill_sergeant.engine import Config, analyze
from pytest_drill_sergeant.findings import Level


def test_finding_carries_the_checks_default_level(assertion_free_test):
    [finding] = analyze([assertion_free_test], Config())

    assert (finding.code, finding.level) == ("DS101", Level.FAIL)


def test_configured_level_overrides_the_default(assertion_free_test):
    [finding] = analyze([assertion_free_test], Config(levels={"DS101": Level.WARN}))

    assert finding.level == Level.WARN


def test_check_configured_off_reports_nothing(assertion_free_test):
    assert analyze([assertion_free_test], Config(levels={"DS101": Level.OFF})) == []
