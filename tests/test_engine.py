"""The engine seam beyond the corpus: what the config changes."""

from pathlib import Path

import pytest

from pytest_drill_sergeant.config import ConfigError, resolve
from pytest_drill_sergeant.engine import Config, analyze
from pytest_drill_sergeant.findings import Level


def test_finding_carries_the_checks_default_level(assertion_free_test):
    [finding] = analyze([assertion_free_test], Config())

    assert (finding.code, finding.level) == ("DS101", Level.FAIL)


def test_interleaved_act_assert_warns_by_default():
    corpus = Path(__file__).parent / "corpus" / "interleaved-act-assert"

    findings = analyze([corpus / "test_bad_two_behaviours.py"], Config())

    assert {(f.code, f.level) for f in findings} == {("DS104", Level.WARN)}


def test_mock_without_spec_warns_by_default():
    corpus = Path(__file__).parent / "corpus" / "mock-without-spec"

    findings = analyze([corpus / "test_bad_mocker_doubles.py"], Config())

    assert {(f.code, f.level) for f in findings} == {("DS302", Level.WARN)}


@pytest.mark.parametrize(("limit", "codes"), [(2, {"DS303"}), (3, set())])
def test_max_mock_setup_sets_how_much_mock_setup_a_test_may_have(
    tmp_path, limit, codes
):
    path = tmp_path / "test_setup.py"
    path.write_text(
        "from unittest import mock\n"
        "\n"
        "def test_total():\n"
        "    repo = mock.create_autospec(Repo, instance=True)\n"
        "    repo.find.return_value = [1, 2]\n"
        "    repo.count.return_value = 2\n"
        "    assert total(repo) == 3\n"
    )

    findings = analyze([path], Config(max_mock_setup=limit))

    assert {f.code for f in findings} == codes


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
        {"drill_sergeant_max_test_lines": "fifty"},
        {"drill_sergeant_max_findings": "-1"},
        {"drill_sergeant_voice": "loudly"},
    ],
    ids=[
        "unknown-key",
        "unknown-code",
        "bad-level",
        "no-level",
        "bad-mode",
        "non-numeric-threshold",
        "negative-number",
        "bad-bool",
    ],
)
def test_bad_config_is_refused(raw):
    with pytest.raises(ConfigError):
        resolve(raw)


@pytest.mark.parametrize(
    "line", ["legacy/*: DS101", "legacy/**: DS1", "test_old.py: DS101, DS1xx"]
)
def test_per_file_ignore_skips_the_named_checks_in_matching_files(tmp_path, line):
    legacy = tmp_path / "legacy" / "test_old.py"
    legacy.parent.mkdir()
    legacy.write_text("def test_old():\n    run()\n")
    config = resolve({"drill_sergeant_per_file_ignores": line}, root=tmp_path)

    assert analyze([legacy], config) == []


def test_per_file_ignore_leaves_other_files_checked(assertion_free_test, tmp_path):
    config = resolve(
        {"drill_sergeant_per_file_ignores": "legacy/*: DS101"}, root=tmp_path
    )

    [finding] = analyze([assertion_free_test], config)

    assert finding.code == "DS101"


def test_per_file_ignore_globs_are_relative_to_the_config_root(tmp_path, monkeypatch):
    legacy = tmp_path / "legacy" / "test_old.py"
    legacy.parent.mkdir()
    legacy.write_text("def test_old():\n    run()\n")
    monkeypatch.chdir(legacy.parent)
    config = resolve({"drill_sergeant_per_file_ignores": "legacy/*: DS101"}, tmp_path)

    assert analyze([Path("test_old.py")], config) == []


def test_options_without_the_prefix_are_not_ours_to_refuse():
    assert resolve({"testpaths": "tests", "timeout": "60"}) == Config()


def test_unset_options_take_the_spec_defaults():
    config = resolve({})

    assert (
        config.max_file_lines,
        config.max_test_lines,
        config.max_mock_setup,
        config.duplicate_setup_min_statements,
        config.duplicate_setup_min_tests,
        config.max_findings,
    ) == (500, 50, 10, 3, 3, 25)
    assert config.category_markers == ("unit", "integration", "e2e")
    assert config.source_dirs == ()
    assert (config.voice, config.inline_waivers, config.cache) == (True, True, True)


def test_every_spec_option_is_known_and_typed(tmp_path):
    (tmp_path / "lib").mkdir()
    (tmp_path / "app").mkdir()

    config = resolve(
        {
            "drill_sergeant_mode": "warn",
            "drill_sergeant_levels": "",
            "drill_sergeant_per_file_ignores": "",
            "drill_sergeant_max_file_lines": "800",
            "drill_sergeant_max_test_lines": "80",
            "drill_sergeant_max_mock_setup": "4",
            "drill_sergeant_duplicate_setup_min_statements": "5",
            "drill_sergeant_duplicate_setup_min_tests": "2",
            "drill_sergeant_category_markers": "unit slow",
            "drill_sergeant_source_dirs": "lib\napp",
            "drill_sergeant_voice": "false",
            "drill_sergeant_max_findings": "0",
            "drill_sergeant_inline_waivers": "no",
            "drill_sergeant_cache": "0",
        },
        root=tmp_path,
    )

    assert (
        config.max_file_lines,
        config.max_test_lines,
        config.max_mock_setup,
        config.duplicate_setup_min_statements,
        config.duplicate_setup_min_tests,
        config.max_findings,
    ) == (800, 80, 4, 5, 2, 0)
    assert config.category_markers == ("unit", "slow")
    assert config.source_dirs == ("lib", "app")
    assert (config.voice, config.inline_waivers, config.cache) == (False, False, False)


def test_typed_values_from_toml_or_pytest_resolve_too():
    config = resolve(
        {
            "drill_sergeant_max_file_lines": 900,
            "drill_sergeant_voice": False,
            "drill_sergeant_category_markers": ["unit", "smoke"],
        }
    )

    assert (config.max_file_lines, config.voice) == (900, False)
    assert config.category_markers == ("unit", "smoke")
