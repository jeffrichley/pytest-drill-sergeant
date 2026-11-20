import pytest

SECTION = "= drill sergeant ="


def test_plugin_is_active_once_installed_and_leaves_a_clean_run_passing(
    drill, pytester
):
    pytester.makepyfile("def test_ok():\n    assert sorted([2, 1]) == [1, 2]\n")

    result = drill()

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK
    assert SECTION in result.stdout.str()


def test_passing_tests_with_fail_findings_exit_1_and_still_run(drill, lazy_test):
    result = drill()

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert "test_lazy.py:1: DS101" in result.stdout.str()


def test_failing_tests_keep_pytests_exit_code(drill, lazy_test, failing_test):
    result = drill()

    result.assert_outcomes(passed=1, failed=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED


def test_findings_section_comes_after_the_test_results(drill, lazy_test, failing_test):
    out = drill().stdout.str()

    assert (
        out.index("= FAILURES =")
        < out.index("short test summary info")
        < out.index(SECTION)
        < out.index("DS101")
    )


def test_no_test_item_is_added_for_the_findings(drill, lazy_test):
    result = drill("--collect-only", "-q")

    assert "1 test collected" in result.stdout.str()


def test_collecting_only_leaves_the_exit_code(drill, lazy_test):
    assert drill("--collect-only").ret == pytest.ExitCode.OK


def test_warn_mode_shows_findings_and_leaves_the_exit_code(drill, pytester, lazy_test):
    pytester.makeini("[pytest]\ndrill_sergeant_mode = warn\n")

    result = drill()

    assert result.ret == pytest.ExitCode.OK
    assert "test_lazy.py:1: DS101" in result.stdout.str()


def test_off_mode_turns_the_plugin_off(drill, pytester, lazy_test):
    pytester.makeini("[pytest]\ndrill_sergeant_mode = off\n")

    result = drill()

    assert result.ret == pytest.ExitCode.OK
    assert SECTION not in result.stdout.str()


def test_disabling_the_plugin_turns_it_off(drill, lazy_test):
    result = drill("-p", "no:drill_sergeant")

    assert result.ret == pytest.ExitCode.OK
    assert SECTION not in result.stdout.str()


@pytest.mark.parametrize(
    "ini",
    [
        "drill_sergeant_mode = loud",
        "drill_sergeant_max_findings = lots",
        "drill_sergeant_voice = maybe",
        "drill_sergeant_levels = DS999=warn",
        "drill_sergeant_bogus = 1",
    ],
    ids=["bad-mode", "non-numeric-number", "bad-bool", "unknown-code", "unknown-key"],
)
def test_bad_config_is_a_usage_error(drill, pytester, lazy_test, ini):
    pytester.makeini(f"[pytest]\n{ini}\n")

    assert drill().ret == pytest.ExitCode.USAGE_ERROR


def test_only_files_with_collected_tests_are_analysed(drill, lazy_file, lazy_test):
    lazy_file("test_other.py", "test_other")
    lazy_file("helper.py", "test_helper")

    out = drill("test_lazy.py").stdout.str()

    assert "test_lazy.py:1: DS101" in out
    assert "test_other.py" not in out
    assert "helper.py" not in out


def test_files_whose_tests_are_all_deselected_are_not_analysed(
    drill, lazy_file, lazy_test
):
    lazy_file("test_other.py", "test_other")

    out = drill("-k", "lazy").stdout.str()

    assert "test_lazy.py:1: DS101" in out
    assert "test_other.py" not in out


def test_each_finding_is_reported_once(drill, lazy_test):
    result = drill()

    assert result.stdout.str().count("test_lazy.py:1: DS101") == 1


def test_per_file_ignores_are_relative_to_the_config_file(drill, pytester, lazy_file):
    pytester.makeini("[pytest]\ndrill_sergeant_per_file_ignores = legacy/*: DS1\n")
    lazy_file("legacy/test_old.py", "test_old")

    result = drill()

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK


def test_shows_the_first_25_findings_then_counts_the_rest(drill, lazy_file):
    lazy_file("test_many.py", *(f"test_{n}" for n in range(27)))

    result = drill()

    out = result.stdout.str()
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert out.count(": DS101") == 25
    assert "27 findings" in out
    assert "and 2 more" in out


def test_max_findings_sets_the_cap(drill, pytester, lazy_file):
    pytester.makeini("[pytest]\ndrill_sergeant_max_findings = 1\n")
    lazy_file("test_many.py", *(f"test_{n}" for n in range(3)))

    out = drill().stdout.str()

    assert out.count(": DS101") == 1
    assert "and 2 more" in out


def test_max_findings_0_shows_every_finding(drill, pytester, lazy_file):
    pytester.makeini("[pytest]\ndrill_sergeant_max_findings = 0\n")
    lazy_file("test_many.py", *(f"test_{n}" for n in range(27)))

    out = drill().stdout.str()

    assert out.count(": DS101") == 27
    assert "more, run" not in out


def test_under_xdist_findings_are_reported_once_by_the_controller(drill, lazy_test):
    result = drill("-p", "xdist", "-n", "2")

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert result.stdout.str().count("test_lazy.py:1: DS101") == 1


def test_a_module_contributing_only_doctests_is_not_analysed(drill, pytester):
    pytester.makepyfile(
        mod='''
        def double(n):
            """
            >>> double(2)
            4
            """
            return n * 2

        def test_lookalike():
            print("hi")
        '''
    )

    result = drill("--doctest-modules")

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.OK


def test_under_xdist_files_outside_the_rootdir_are_analysed(drill, pytester, lazy_test):
    pytester.mkdir("elsewhere")

    result = drill("-p", "xdist", "-n", "1", "--rootdir=elsewhere", "test_lazy.py")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert "test_lazy.py:1: DS101" in result.stdout.str()


@pytest.mark.parametrize(
    "ini",
    [
        "drill_sergeant_bogus = 1",
        "drill_sergeant_levels = DS101=loud",
        "drill_sergeant_max_findings = lots",
    ],
    ids=["unknown-key", "bad-level", "non-numeric-number"],
)
def test_cli_and_plugin_refuse_bad_config_in_the_same_line(
    cli, drill, pytester, lazy_test, ini
):
    config = pytester.makeini(f"[pytest]\n{ini}\n")

    cli_line = cli("check", "--config", str(config), str(lazy_test)).stderr.strip()

    assert cli_line.startswith("drill-sergeant: ")
    assert cli_line in drill().stderr.str()


def _section(out: str) -> str:
    return out[out.index("drill sergeant") :].split("\n", 1)[1]


def test_colour_follows_pytests_own_setting(drill, lazy_test):
    coloured = _section(drill("--color=yes").stdout.str())
    plain = _section(drill("--color=no").stdout.str())

    assert "\x1b[" in coloured
    assert "\x1b" not in plain


def test_findings_section_wraps_to_pytests_terminal_width(
    drill, lazy_file, monkeypatch, wrapped
):
    monkeypatch.setenv("COLUMNS", "60")
    lazy_file("test_long.py", f"test_{'very_' * 10}long")

    section = _section(drill().stdout.str())

    location = next(line for line in section.splitlines() if "DS101" in line)
    assert (
        f"test_long.py:1: DS101 no-real-assertion [fail] in test_{'very_' * 10}long"
        in location
    )
    continuations, following = wrapped(section, "Found:")
    assert continuations
    assert following.lstrip().startswith("Why:")


def test_waived_finding_leaves_the_run_passing_and_is_tallied(drill, pytester):
    pytester.makepyfile(
        test_waived="def test_waived():  # drill: waive DS101 -- smoke test\n"
        "    print('hi')\n"
    )

    result = drill()

    assert result.ret == pytest.ExitCode.OK
    assert "1 waived" in result.stdout.str()


def test_reasonless_waiver_fails_the_run_and_waives_nothing(drill, pytester):
    pytester.makepyfile(
        test_waived="def test_waived():  # drill: waive DS101\n    print('hi')\n"
    )

    result = drill()

    result.assert_outcomes(passed=1)
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    out = result.stdout.str()
    assert "test_waived.py:1: DS001" in out
    assert "test_waived.py:1: DS101" in out
