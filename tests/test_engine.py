"""The engine seam beyond the corpus: what the config changes."""

from pathlib import Path

import pytest

from pytest_drill_sergeant.config import ConfigError, resolve
from pytest_drill_sergeant.engine import Config, analyze
from pytest_drill_sergeant.findings import Level

pytestmark = pytest.mark.unit


def test_finding_carries_the_checks_default_level(unseeded_random_test):
    [finding] = analyze([unseeded_random_test], Config())

    assert (finding.code, finding.level) == ("DS803", Level.FAIL)


@pytest.mark.parametrize("level", [Level.WARN, Level.FAIL])
def test_check_off_by_default_reports_at_the_level_configured(
    assertion_free_test, level
):
    [finding] = analyze([assertion_free_test], Config(levels={"DS101": level}))

    assert (finding.code, finding.level) == ("DS101", level)


@pytest.mark.parametrize(("limit", "codes"), [(2, {"DS303"}), (3, set())])
def test_max_mock_setup_sets_how_much_mock_setup_a_test_may_have(
    tmp_path, unit_mark, limit, codes
):
    path = tmp_path / "test_setup.py"
    path.write_text(
        "from unittest import mock\n"
        "\n"
        "def test_total():\n"
        "    repo = mock.create_autospec(Repo, instance=True)\n"
        "    repo.find.return_value = [1, 2]\n"
        "    repo.count.return_value = 2\n"
        "    assert total(repo) == 3\n" + unit_mark
    )

    findings = analyze(
        [path], Config(max_mock_setup=limit, levels={"DS303": Level.FAIL})
    )

    assert {f.code for f in findings} == codes


def test_configured_level_overrides_the_default(unseeded_random_test):
    [finding] = analyze([unseeded_random_test], Config(levels={"DS803": Level.WARN}))

    assert finding.level == Level.WARN


@pytest.mark.parametrize(
    ("raw", "codes"),
    [({}, set()), ({"drill_sergeant_levels": "DS108=warn"}, {"DS108"})],
    ids=["default", "enabled"],
)
def test_aaa_comment_check_is_off_until_enabled_through_levels(raw, codes):
    path = Path(__file__).parent / "corpus" / "aaa-comments" / "test_bad_no_comments.py"

    findings = analyze([path], resolve(raw))

    assert {f.code for f in findings} == codes


def test_check_configured_off_reports_nothing(unseeded_random_test):
    assert analyze([unseeded_random_test], Config(levels={"DS803": Level.OFF})) == []


def test_warn_mode_reports_fail_findings_as_warn(unseeded_random_test):
    config = resolve({"drill_sergeant_mode": "warn"})

    [finding] = analyze([unseeded_random_test], config)

    assert finding.level == Level.WARN


def test_off_mode_reports_nothing(unseeded_random_test):
    assert (
        analyze([unseeded_random_test], resolve({"drill_sergeant_mode": "off"})) == []
    )


def test_fail_mode_keeps_configured_levels(unseeded_random_test):
    config = resolve(
        {"drill_sergeant_mode": "fail", "drill_sergeant_levels": "DS803=warn"}
    )

    [finding] = analyze([unseeded_random_test], config)

    assert finding.level == Level.WARN


def test_family_prefix_sets_the_level_of_the_whole_family(unseeded_random_test):
    config = resolve({"drill_sergeant_levels": "DS8xx=off"})

    assert analyze([unseeded_random_test], config) == []


@pytest.mark.parametrize(
    "lines", [["DS8=off", "DS803=warn"], ["DS803=warn", "DS8=off"]]
)
def test_most_specific_level_wins_whatever_the_order(unseeded_random_test, lines):
    config = resolve({"drill_sergeant_levels": lines})

    [finding] = analyze([unseeded_random_test], config)

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
    "line", ["legacy/*: DS803", "legacy/**: DS8", "test_old.py: DS803, DS8xx"]
)
def test_per_file_ignore_skips_the_named_checks_in_matching_files(
    tmp_path, unseeded_random_test, line
):
    legacy = tmp_path / "legacy" / "test_old.py"
    legacy.parent.mkdir()
    unseeded_random_test.rename(legacy)
    config = resolve({"drill_sergeant_per_file_ignores": line}, root=tmp_path)

    assert analyze([legacy], config) == []


def test_per_file_ignore_leaves_other_files_checked(unseeded_random_test, tmp_path):
    config = resolve(
        {"drill_sergeant_per_file_ignores": "legacy/*: DS803"}, root=tmp_path
    )

    [finding] = analyze([unseeded_random_test], config)

    assert finding.code == "DS803"


def test_per_file_ignore_globs_are_relative_to_the_config_root(
    tmp_path, monkeypatch, unseeded_random_test
):
    legacy = tmp_path / "legacy" / "test_old.py"
    legacy.parent.mkdir()
    unseeded_random_test.rename(legacy)
    monkeypatch.chdir(legacy.parent)
    config = resolve({"drill_sergeant_per_file_ignores": "legacy/*: DS803"}, tmp_path)

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


@pytest.mark.parametrize(
    "config",
    [
        Config(duplicate_setup_min_tests=2, levels={"DS501": Level.FAIL}),
        Config(duplicate_setup_min_statements=2, levels={"DS501": Level.FAIL}),
    ],
    ids=["two-tests", "two-statements"],
)
def test_copy_paste_setup_thresholds_come_from_the_config(config):
    corpus = Path(__file__).parent / "corpus" / "copy-paste-setup"

    findings = analyze([corpus / "test_good_below_the_thresholds.py"], config)

    assert {(f.code, f.line) for f in findings} == {("DS501", 11)}


def test_cross_file_findings_do_not_depend_on_the_order_files_are_given(
    pasted_across_files,
):
    config = Config(levels={"DS501": Level.FAIL})

    assert analyze(pasted_across_files, config) == analyze(
        pasted_across_files[::-1], config
    )


def test_per_file_ignore_leaves_a_file_out_of_cross_file_comparison(
    pasted_across_files,
):
    root = pasted_across_files[0].parent
    config = resolve(
        {
            "drill_sergeant_levels": "DS501=fail",
            "drill_sergeant_per_file_ignores": "*limits.py: DS501",
        },
        root,
    )

    assert analyze(pasted_across_files, config) == []


def test_configured_level_applies_to_cross_file_findings(pasted_across_files):
    findings = analyze(pasted_across_files, Config(levels={"DS501": Level.WARN}))

    assert {(f.code, f.level) for f in findings} == {("DS501", Level.WARN)}


@pytest.mark.parametrize(
    ("threshold", "codes"),
    [
        ({"max_test_lines": 3}, set()),
        ({"max_test_lines": 2}, {"DS105"}),
        ({"max_file_lines": 7}, set()),
        ({"max_file_lines": 6}, {"DS106"}),
    ],
)
def test_thresholds_set_how_long_a_test_and_a_file_may_be(
    tmp_path, unit_mark, threshold, codes
):
    """The file is the test's three lines and the four of `unit_mark`."""
    path = tmp_path / "test_add.py"
    path.write_text(
        "def test_add(calc):\n    total = calc.add(1, 2)\n    assert total == 3\n"
        + unit_mark
    )

    findings = analyze([path], Config(**threshold, levels={"DS105": Level.FAIL}))

    assert {f.code for f in findings} == codes


@pytest.mark.parametrize(
    "source",
    [
        "class TestLoans:\n    def test_lend(self, library):\n"
        "        assert library.lend(1).days == 21\n",
        "from shop import loans\n\ndef test_lend():\n    assert loans(1) == 21\n\n"
        "def test_renew():\n    assert loans(2, renewed=True) == 42\n",
    ],
    ids=["class", "module-level-tests"],
)
def test_long_file_split_never_moves_tests_to_the_file_itself(write_test_file, source):
    path = write_test_file(source, "test_loans.py")

    [finding] = analyze([path], Config(max_file_lines=2))

    assert finding.code == "DS106"
    assert "to `test_loans.py`" not in finding.fix


# DS901 is off by default, a convention a project opts into.
MARKERS_ON = {"DS901": Level.FAIL}


@pytest.mark.parametrize(
    ("markers", "codes"), [(("e2e",), {"DS901"}), (("smoke",), set())]
)
def test_category_markers_come_from_the_config(write_test_file, markers, codes):
    path = write_test_file(
        "import pytest\n\n@pytest.mark.smoke\ndef test_total():\n"
        "    assert total([1, 2]) == 3\n"
    )

    findings = analyze([path], Config(category_markers=markers, levels=MARKERS_ON))

    assert {f.code for f in findings} == codes


def test_no_configured_category_markers_flags_nothing(unmarked_test_at):
    path = unmarked_test_at("test_total.py")

    assert analyze([path], Config(category_markers=(), levels=MARKERS_ON)) == []


def test_category_marker_fix_names_the_nearest_category_directory(
    tmp_path, unmarked_test_at
):
    path = unmarked_test_at("e2e/integration/test_total.py")

    [finding] = analyze([path], Config(root=tmp_path, levels=MARKERS_ON))

    assert finding.code == "DS901"
    assert "`@pytest.mark.integration`" in finding.fix
    assert "e2e" not in finding.fix


def test_category_marker_fix_lists_every_marker_when_no_directory_below_the_root_names_one(
    tmp_path, unmarked_test_at
):
    """The config root's own name is not a directory the file is in."""
    path = unmarked_test_at("unit/checks/test_total.py")

    [finding] = analyze([path], Config(root=tmp_path / "unit", levels=MARKERS_ON))

    assert all(
        f"`@pytest.mark.{m}`" in finding.fix for m in ("unit", "integration", "e2e")
    )


def test_category_marker_fix_names_the_one_configured_marker(
    tmp_path, unmarked_test_at
):
    path = unmarked_test_at("test_total.py")

    [finding] = analyze(
        [path], Config(root=tmp_path, category_markers=("unit",), levels=MARKERS_ON)
    )

    assert "add `@pytest.mark.unit` to" in finding.fix


def test_category_marker_fix_reads_directory_names_in_any_case(
    tmp_path, unmarked_test_at
):
    path = unmarked_test_at("tests/Unit/test_total.py")

    [finding] = analyze([path], Config(root=tmp_path, levels=MARKERS_ON))

    assert "`@pytest.mark.unit`" in finding.fix
    assert "e2e" not in finding.fix
