import shutil
from pathlib import Path

import pytest

CORPUS = Path(__file__).parent / "corpus"


def test_help_names_the_command(cli):
    result = cli("--help")

    assert result.exit_code == 0, result.output
    assert "drill-sergeant" in result.output


def test_check_exits_zero_on_a_clean_file(cli, tmp_path):
    (tmp_path / "test_ok.py").write_text(
        "def test_ok():\n    assert sum([1, 1]) == 2\n"
    )

    result = cli("check", "test_ok.py")

    assert result.exit_code == 0, result.output


def test_check_exits_nonzero_and_locates_the_finding(cli, assertion_free_test):
    result = cli("check", "test_it.py")

    assert result.exit_code == 1, result.output
    assert "test_it.py:1" in result.output
    assert "DS101" in result.output


def test_check_finds_test_files_in_a_directory_and_skips_the_rest(cli, tmp_path):
    for name in ("test_a.py", "b_test.py", "helpers.py", ".venv/test_vendored.py"):
        (tmp_path / "suite" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")

    result = cli("check", "suite")

    assert "test_a.py:1" in result.output
    assert "b_test.py:1" in result.output
    assert "helpers.py" not in result.output
    assert "test_vendored.py" not in result.output


def test_check_takes_test_files_by_the_configs_python_files(cli, tmp_path):
    for name in ("check_a.py", "test_b.py"):
        (tmp_path / "suite" / name).parent.mkdir(exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\npython_files = check_*.py\n")

    result = cli("check", "suite")

    assert "check_a.py:1" in result.output
    assert "test_b.py" not in result.output


def test_check_skips_the_configs_norecursedirs(cli, tmp_path):
    for name in ("legacy/test_old.py", "current/test_new.py"):
        (tmp_path / "suite" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\nnorecursedirs = ["legacy"]\n'
    )

    result = cli("check", "suite")

    assert "test_new.py:1" in result.output
    assert "test_old.py" not in result.output


def test_check_refuses_a_missing_path(cli):
    assert cli("check", "nowhere").exit_code == 2


def test_check_refuses_a_file_that_does_not_parse(cli, tmp_path):
    (tmp_path / "test_broken.py").write_text("def test_broken(:\n")

    assert cli("check", "test_broken.py").exit_code == 2


# Each way pytest can hold the config, setting warn mode.
WARN_CONFIGS = {
    "pytest.ini": "[pytest]\ndrill_sergeant_mode = warn\n",
    "pyproject.toml": '[tool.pytest.ini_options]\ndrill_sergeant_mode = "warn"\n',
    "tox.ini": "[pytest]\ndrill_sergeant_mode = warn\n",
    "setup.cfg": "[tool:pytest]\ndrill_sergeant_mode = warn\n",
    ".pytest.ini": "[pytest]\ndrill_sergeant_mode = warn\n",
    "pytest.toml": '[pytest]\ndrill_sergeant_mode = "warn"\n',
}


@pytest.mark.parametrize("name", WARN_CONFIGS)
def test_check_reads_the_config_pytest_would(cli, tmp_path, assertion_free_test, name):
    (tmp_path / name).write_text(WARN_CONFIGS[name])

    result = cli("check", "test_it.py")

    assert result.exit_code == 0, result.output
    assert "DS101" in result.output


def test_check_reads_pytest_9_native_toml(cli, tmp_path, assertion_free_test):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest]\ndrill_sergeant_mode = "warn"\n'
    )

    assert cli("check", "test_it.py").exit_code == 0


def test_check_searches_upward_from_the_given_paths(cli, tmp_path):
    deep = tmp_path / "pkg" / "tests"
    deep.mkdir(parents=True)
    (deep / "test_it.py").write_text("def test_it():\n    run()\n")
    (tmp_path / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])

    assert cli("check", "pkg/tests").exit_code == 0


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("pyproject.toml", "[tool.ruff]\nline-length = 88\n"),
        ("tox.ini", "[tox]\nenvlist = py311\n"),
        ("setup.cfg", "[metadata]\nname = x\n"),
    ],
)
def test_check_passes_over_files_without_a_pytest_section(cli, tmp_path, name, content):
    deep = tmp_path / "pkg"
    deep.mkdir()
    (deep / "test_it.py").write_text("def test_it():\n    run()\n")
    (deep / name).write_text(content)
    (tmp_path / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])

    assert cli("check", "pkg").exit_code == 0


def test_the_nearest_config_wins(cli, tmp_path):
    deep = tmp_path / "pkg"
    deep.mkdir()
    (deep / "test_it.py").write_text("def test_it():\n    run()\n")
    (deep / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])

    assert cli("check", "pkg").exit_code == 1


def test_config_option_overrides_discovery(cli, tmp_path, assertion_free_test):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])

    assert cli("check", "--config", "ci/pytest.ini", "test_it.py").exit_code == 0


def test_per_file_ignore_globs_are_relative_to_the_config_file(cli, tmp_path):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "test_old.py").write_text("def test_old():\n    run()\n")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\ndrill_sergeant_per_file_ignores =\n    legacy/*: DS101\n"
    )

    result = cli("check", str(legacy / "test_old.py"))

    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "ini",
    [
        "drill_sergeant_bogus = 1",
        "drill_sergeant_levels = DS999=warn",
        "drill_sergeant_levels = DS101=loud",
        "drill_sergeant_max_test_lines = fifty",
    ],
    ids=["unknown-key", "unknown-code", "bad-level", "non-numeric-threshold"],
)
def test_check_refuses_bad_config(cli, tmp_path, assertion_free_test, ini):
    (tmp_path / "pytest.ini").write_text(f"[pytest]\n{ini}\n")

    assert cli("check", "test_it.py").exit_code == 2


def test_check_refuses_a_missing_config_file(cli, assertion_free_test):
    assert cli("check", "--config", "nowhere.ini", "test_it.py").exit_code == 2


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("pyproject.toml", "[tool.pytest\n"),
        ("pytest.ini", "drill_sergeant_mode = warn\n"),
        (
            "pyproject.toml",
            "[tool.pytest]\nminversion = '9'\n[tool.pytest.ini_options]\nx = 1\n",
        ),
    ],
    ids=["broken-toml", "no-section-header", "both-pytest-tables"],
)
def test_check_refuses_a_config_file_that_does_not_parse(
    cli, tmp_path, assertion_free_test, name, content
):
    (tmp_path / name).write_text(content)

    assert cli("check", "test_it.py").exit_code == 2


def test_no_environment_variable_configures_drill_sergeant(
    cli, assertion_free_test, monkeypatch
):
    monkeypatch.setenv("DRILL_SERGEANT_MODE", "off")
    monkeypatch.setenv("drill_sergeant_mode", "off")

    assert cli("check", "test_it.py").exit_code == 1


def test_no_command_line_flag_configures_drill_sergeant(cli, assertion_free_test):
    assert cli("check", "--mode", "off", "test_it.py").exit_code == 2


def test_voice_off_keeps_found_why_fix_and_drops_the_voice(
    cli, tmp_path, assertion_free_test
):
    voiced = cli("check", "test_it.py").output
    (tmp_path / "pytest.ini").write_text("[pytest]\ndrill_sergeant_voice = false\n")

    plain = cli("check", "test_it.py").output

    facts = [
        line
        for line in voiced.splitlines()
        if line.lstrip().startswith(("Found:", "Why:", "Fix:"))
    ]
    assert len(facts) == 3
    assert all(line in plain.splitlines() for line in facts)
    assert "DRILL SERGEANT" not in plain
    assert "DISMISSED" not in plain
    assert not any(line.startswith('    "') for line in plain.splitlines())


LONG_LOCATION = (
    f"test_long.py:1: DS101 no-real-assertion [fail] in test_{'very_' * 10}long"
)


def test_a_narrow_terminal_wraps_each_fact_under_its_text_and_keeps_the_location_whole(
    cli, long_named_test, monkeypatch, wrapped
):
    monkeypatch.setenv("COLUMNS", "60")

    output = cli("check", "test_long.py").output

    location, *rest = [line for line in output.splitlines() if "DS101" in line]
    assert LONG_LOCATION in location
    assert not rest
    for label, after in [("Found:", "Why:"), ("Why:", "Fix:"), ("Fix:", "")]:
        continuations, following = wrapped(output, label)
        assert continuations, label
        assert following.lstrip().startswith(after), label
    assert max(len(line) for line in output.splitlines() if line != location) <= 60


def test_check_writes_no_escape_codes_when_colour_is_off(cli, assertion_free_test):
    assert "\x1b" not in cli("check", "test_it.py").output


def test_forced_colour_styles_the_report_and_links_the_location_to_its_file(
    cli, assertion_free_test, monkeypatch
):
    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")

    output = cli("check", "test_it.py").output

    assert "\x1b[" in output
    assert f";{assertion_free_test.resolve().as_uri()}\x1b\\test_it.py:1" in output


# A change to the report changes golden/check.txt: rerun
# `drill-sergeant check --show-waived suite` over a copy of the corpus with
# NO_COLOR=1 COLUMNS=100, and review the diff.
def test_check_output_matches_the_golden_report(cli, tmp_path):
    golden = Path(__file__).parent / "golden" / "check.txt"
    suite = tmp_path / "suite"
    shutil.copytree(CORPUS, suite)

    result = cli("check", "--show-waived", "suite")

    assert result.output == golden.read_text()


def test_waived_findings_leave_the_exit_code_and_are_tallied(cli, waived_test):
    result = cli("check", "test_waived.py")

    assert result.exit_code == 0, result.output
    assert "1 waived" in result.output
    assert "smoke test" not in result.output


def test_tally_counts_waived_findings_beside_the_findings_that_stand(
    cli, waived_test, assertion_free_test
):
    result = cli("check", "test_waived.py", "test_it.py")

    assert result.exit_code == 1, result.output
    assert "1 waived" in result.output.splitlines()[-1]


def test_show_waived_lists_each_waived_finding_with_its_reason(cli, waived_test):
    result = cli("check", "--show-waived", "test_waived.py")

    assert result.exit_code == 0, result.output
    [listed] = [line for line in result.output.splitlines() if "DS101" in line]
    assert "test_waived.py:1" in listed
    assert "smoke test" in result.output


def test_with_inline_waivers_off_the_cli_reports_the_waived_finding(
    cli, tmp_path, waived_test
):
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\ndrill_sergeant_inline_waivers = false\n"
    )

    result = cli("check", "test_waived.py")

    assert result.exit_code == 1, result.output
    assert "0 waived" in result.output


def test_check_caches_under_pytests_cache_dir_at_the_config_root(
    cli, tmp_path, assertion_free_test
):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")

    cli("check", str(assertion_free_test))

    assert (tmp_path / ".pytest_cache" / "d" / "drill-sergeant").is_dir()


def test_check_follows_the_configs_cache_dir(cli, tmp_path, assertion_free_test):
    (tmp_path / "pytest.ini").write_text("[pytest]\ncache_dir = build/cache\n")

    cli("check", str(assertion_free_test))

    assert (tmp_path / "build" / "cache" / "d" / "drill-sergeant").is_dir()


def test_cache_dir_the_check_makes_is_ignored_by_git(
    cli, tmp_path, assertion_free_test
):
    cli("check", str(assertion_free_test))

    assert (tmp_path / ".pytest_cache" / ".gitignore").read_text().strip().endswith("*")


def test_check_with_cache_off_writes_no_cache(cli, tmp_path, assertion_free_test):
    (tmp_path / "pytest.ini").write_text("[pytest]\ndrill_sergeant_cache = false\n")

    result = cli("check", str(assertion_free_test))

    assert result.exit_code == 1
    assert not (tmp_path / ".pytest_cache").exists()


def test_warm_check_with_nothing_changed_writes_nothing(
    cli, tmp_path, assertion_free_test, watch
):
    cli("check", str(assertion_free_test))
    written = watch(tmp_path / ".pytest_cache")

    result = cli("check", str(assertion_free_test))

    assert result.exit_code == 1
    assert (tmp_path / ".pytest_cache" / "d" / "drill-sergeant").is_dir()
    assert written() == []
