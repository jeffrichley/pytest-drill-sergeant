"""The engine seam beyond the corpus: what the config changes."""

import pytest

from pytest_drill_sergeant.config import ConfigError, resolve
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


def test_warn_mode_reports_fail_findings_as_warn(assertion_free_test):
    config = resolve({"drill_sergeant_mode": "warn"})

    [finding] = analyze([assertion_free_test], config)

    assert finding.level == Level.WARN


def test_off_mode_reports_nothing(assertion_free_test):
    assert analyze([assertion_free_test], resolve({"drill_sergeant_mode": "off"})) == []


def test_fail_mode_keeps_configured_levels(assertion_free_test):
    config = resolve(
        {"drill_sergeant_mode": "fail", "drill_sergeant_levels": "DS101=warn"}
    )

    [finding] = analyze([assertion_free_test], config)

    assert finding.level == Level.WARN


def test_family_prefix_sets_the_level_of_the_whole_family(assertion_free_test):
    config = resolve({"drill_sergeant_levels": "DS1xx=off"})

    assert analyze([assertion_free_test], config) == []


@pytest.mark.parametrize(
    "lines", [["DS1=off", "DS101=warn"], ["DS101=warn", "DS1=off"]]
)
def test_most_specific_level_wins_whatever_the_order(assertion_free_test, lines):
    config = resolve({"drill_sergeant_levels": lines})

    [finding] = analyze([assertion_free_test], config)

    assert finding.level == Level.WARN


@pytest.mark.parametrize(
    "raw",
    [
        {"drill_sergeant_bogus": "1"},
        {"drill_sergeant_levels": "DS999=warn"},
        {"drill_sergeant_levels": "DS101=loud"},
        {"drill_sergeant_levels": "DS101"},
        {"drill_sergeant_mode": "sometimes"},
    ],
    ids=["unknown-key", "unknown-code", "bad-level", "no-level", "bad-mode"],
)
def test_bad_config_is_refused(raw):
    with pytest.raises(ConfigError):
        resolve(raw)


def test_options_without_the_prefix_are_not_ours_to_refuse():
    assert resolve({"testpaths": "tests", "timeout": "60"}) == Config()
