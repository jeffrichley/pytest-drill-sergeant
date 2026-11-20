import shutil
from pathlib import Path

import pytest

from pytest_drill_sergeant.checks import CHECKS

pytestmark = pytest.mark.integration

GOLDEN = Path(__file__).parent / "golden"


def test_help_names_the_command(cli):
    result = cli("--help")

    assert result.exit_code == 0, result.output
    assert "drill-sergeant" in result.output


def test_check_exits_zero_on_a_clean_file(cli, clean_test):
    result = cli("check", "test_ok.py")

    assert result.exit_code == 0, result.output


def test_check_exits_nonzero_and_locates_the_finding(cli, assertion_free_test):
    result = cli("check", "test_it.py")

    assert result.exit_code == 1, result.output
    assert "test_it.py:1" in result.output
    assert "DS101" in result.output


def test_check_finds_test_files_in_a_directory_and_skips_the_rest(
    cli, cli_ini, tmp_path
):
    cli_ini()
    for name in ("test_a.py", "b_test.py", "helpers.py", ".venv/test_vendored.py"):
        (tmp_path / "suite" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")

    result = cli("check", "suite")

    assert "test_a.py:1" in result.output
    assert "b_test.py:1" in result.output
    assert "helpers.py" not in result.output
    assert "test_vendored.py" not in result.output


def test_check_takes_test_files_by_the_configs_python_files(cli, cli_ini, tmp_path):
    for name in ("check_a.py", "test_b.py"):
        (tmp_path / "suite" / name).parent.mkdir(exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")
    cli_ini("python_files = check_*.py")

    result = cli("check", "suite")

    assert "check_a.py:1" in result.output
    assert "test_b.py" not in result.output


def test_check_skips_the_configs_norecursedirs(cli, tmp_path):
    for name in ("legacy/test_old.py", "current/test_new.py"):
        (tmp_path / "suite" / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "suite" / name).write_text("def test_x():\n    run()\n")
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'norecursedirs = ["legacy"]\n'
        'drill_sergeant_levels = ["DS101=fail"]\n'
    )

    result = cli("check", "suite")

    assert "test_new.py:1" in result.output
    assert "test_old.py" not in result.output


def test_check_refuses_a_missing_path(cli):
    assert cli("check", "nowhere").exit_code == 2


def test_explain_refuses_an_unknown_code_naming_it(cli):
    result = cli("explain", "DS999")

    assert result.exit_code == 2
    assert "DS999" in result.stderr


def test_check_refuses_a_file_that_does_not_parse(cli, tmp_path):
    (tmp_path / "test_broken.py").write_text("def test_broken(:\n")

    assert cli("check", "test_broken.py").exit_code == 2


# A test file found in a directory that can't be read: one gone since it was found
# (a link to nowhere), and one whose read fails some other way (a link to itself).
UNREADABLE_TARGETS = {"vanished": "nowhere.py", "link-loop": "test_x.py"}


@pytest.mark.parametrize("target", UNREADABLE_TARGETS.values(), ids=UNREADABLE_TARGETS)
def test_check_refuses_a_test_file_it_cannot_read_naming_it(cli, tmp_path, target):
    (tmp_path / "suite").mkdir()
    (tmp_path / "suite" / "test_x.py").symlink_to(target)

    result = cli("check", "suite")

    assert result.exit_code == 2
    assert "test_x.py" in result.stderr


def test_voice_off_keeps_found_why_fix_and_drops_the_voice(
    cli, cli_ini, assertion_free_test
):
    voiced = cli("check", "test_it.py").output
    cli_ini("drill_sergeant_voice = false")

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


def test_a_narrow_terminal_keeps_the_location_whole(cli, long_named_test, monkeypatch):
    monkeypatch.setenv("COLUMNS", "60")

    output = cli("check", "test_long.py").output

    location, *rest = [
        line for line in output.splitlines() if "no-real-assertion" in line
    ]
    assert LONG_LOCATION in location
    assert not rest
    facts = [line for line in output.splitlines() if line != location]
    assert max(len(line) for line in facts) <= 60


@pytest.mark.parametrize(
    ("label", "after"), [("Found:", "Why:"), ("Why:", "Fix:"), ("Fix:", "")]
)
def test_a_narrow_terminal_wraps_each_fact_under_its_text(
    cli, long_named_test, monkeypatch, wrapped, label, after
):
    monkeypatch.setenv("COLUMNS", "60")

    continuations, following = wrapped(cli("check", "test_long.py").output, label)

    assert continuations
    assert following.lstrip().startswith(after)


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


def test_check_reads_production_code_under_src(
    cli, cli_ini, tmp_path, assertion_free_test, special_casing_module
):
    special_casing_module(tmp_path / "src")
    cli_ini(on=("DS403=fail",))

    assert "src/app.py:4: DS403" in cli("check", "test_it.py").output


def test_check_reads_the_configured_source_dirs_instead_of_src(
    cli, cli_ini, tmp_path, assertion_free_test, special_casing_module
):
    special_casing_module(tmp_path / "lib")
    special_casing_module(tmp_path / "src")
    cli_ini("drill_sergeant_source_dirs = lib", on=("DS403=fail",))

    output = cli("check", "test_it.py").output

    assert "lib/app.py:4: DS403" in output
    assert "src/app.py" not in output


def test_without_production_code_the_special_casing_check_is_skipped_with_a_note(
    cli, cli_ini, clean_test
):
    cli_ini(on=("DS403=fail",))

    result = cli("check", "test_ok.py")

    assert result.exit_code == 0, result.output
    assert "DS403" in result.output
    assert "drill_sergeant_source_dirs" in result.output


@pytest.mark.parametrize(
    ("lines", "on"),
    [((), ()), (("drill_sergeant_mode = off",), ("DS403=fail",))],
    ids=["check-off-by-default", "mode-off"],
)
def test_no_note_when_the_special_casing_check_does_not_run(
    cli, cli_ini, assertion_free_test, lines, on
):
    cli_ini(*lines, on=on)

    assert "drill_sergeant_source_dirs" not in cli("check", "test_it.py").output


def test_production_code_is_read_in_full_on_every_run(
    cli, cli_ini, tmp_path, assertion_free_test, special_casing_module
):
    app = special_casing_module(tmp_path / "src")
    cli_ini(on=("DS403=fail",))
    cli("check", "test_it.py")
    with app.open("a") as source:
        source.write("LATE = os.environ.get('PYTEST_CURRENT_TEST')\n")

    output = cli("check", "test_it.py").output

    assert "src/app.py:4: DS403" in output
    assert "src/app.py:5: DS403" in output


# The golden suite is a small fixed suite, apart from the corpus, so only a change to
# the report (or a check firing on its files) changes golden/check.txt. Regenerate it
# with `just golden` and review `git diff tests/golden`.
def test_check_output_matches_the_golden_report(cli, tmp_path):
    shutil.copytree(GOLDEN / "suite", tmp_path / "suite")

    result = cli("check", "--show-waived", "suite")

    assert result.output == (GOLDEN / "check.txt").read_text()


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
    cli, cli_ini, waived_test
):
    cli_ini("drill_sergeant_inline_waivers = false")

    result = cli("check", "test_waived.py")

    assert result.exit_code == 1, result.output
    assert "0 waived" in result.output


def test_check_caches_under_pytests_cache_dir_at_the_config_root(
    cli, tmp_path, assertion_free_test
):
    cli("check", str(assertion_free_test))

    assert (tmp_path / ".pytest_cache" / "d" / "drill-sergeant").is_dir()


def test_check_follows_the_configs_cache_dir(
    cli, cli_ini, tmp_path, assertion_free_test
):
    cli_ini("cache_dir = build/cache")

    cli("check", str(assertion_free_test))

    assert (tmp_path / "build" / "cache" / "d" / "drill-sergeant").is_dir()


def test_cache_dir_the_check_makes_is_ignored_by_git(
    cli, tmp_path, assertion_free_test
):
    cli("check", str(assertion_free_test))

    assert (tmp_path / ".pytest_cache" / ".gitignore").read_text().strip().endswith("*")


def test_check_with_cache_off_writes_no_cache(
    cli, cli_ini, tmp_path, assertion_free_test
):
    cli_ini("drill_sergeant_cache = false")

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


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_explain_prints_the_registrys_rationale_explanation_and_both_examples(
    cli, check
):
    result = cli("explain", check.code)

    assert result.exit_code == 0, result.output
    assert check.why in result.output
    assert check.explain in result.output
    assert check.bad_example in result.output
    assert check.good_example in result.output


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_explain_heads_a_check_with_its_default_level_and_kind(cli, check):
    header = cli("explain", check.code).output.splitlines()[0]

    assert header.endswith(f"[{check.default_level}, {check.kind}]")


def test_explain_with_no_code_lists_every_check(cli):
    result = cli("explain")

    assert result.exit_code == 0, result.output
    listed = [line.split()[:2] for line in result.output.splitlines()]
    assert all([c.code, c.name] in listed for c in CHECKS)


def test_fix_line_ends_with_a_pointer_to_explain(cli, assertion_free_test, monkeypatch):
    monkeypatch.setenv("COLUMNS", "1000")

    output = cli("check", "test_it.py").output

    fix = next(line for line in output.splitlines() if line.lstrip().startswith("Fix:"))
    assert fix.endswith("`drill-sergeant explain DS101`.")
