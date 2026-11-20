import pytest

pytestmark = pytest.mark.integration


# A test with no real assertion: DS101 on line 1, a check at `warn` by default.
ASSERTION_FREE = "def test_it():\n    run()\n"


def outside_cache(paths):
    """The paths not under pytest's cache directory, which a check run writes to."""
    return [p for p in paths if ".pytest_cache" not in p.parts]


def test_try_with_no_checks_named_runs_check_as_it_stands(try_checks, write_test_file):
    write_test_file(ASSERTION_FREE)

    code, output = try_checks(".")

    assert code == 0, output
    assert "DS101" in output


def test_try_turns_the_named_checks_on_at_fail(try_checks, write_test_file):
    write_test_file(ASSERTION_FREE)

    code, output = try_checks("test_it.py", "DS101")

    assert code == 1, output
    assert "DS101" in output


def test_try_keeps_the_projects_levels(
    try_checks, tmp_path, write_test_file, unseeded_random_test
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ndrill_sergeant_levels = ["DS803=off"]\n'
    )

    _, output = try_checks(".", "DS101")

    assert "DS101" in output
    assert "DS803" not in output


def test_try_keeps_the_projects_ini_settings(try_checks, tmp_path, write_test_file):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pytest.ini").write_text("[pytest]\ndrill_sergeant_mode = warn\n")

    code, output = try_checks("test_it.py", "DS101")

    assert code == 0, output
    assert "DS101" in output


def test_try_reads_paths_in_the_config_from_the_projects_root(
    try_checks, tmp_path, write_test_file
):
    (tmp_path / "proj" / "tests" / "legacy").mkdir(parents=True)
    write_test_file(ASSERTION_FREE, "proj/tests/test_new.py")
    write_test_file(ASSERTION_FREE, "proj/tests/legacy/test_old.py")
    (tmp_path / "proj" / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'drill_sergeant_per_file_ignores = ["tests/legacy/**: DS101"]\n'
    )

    _, output = try_checks("proj/tests", "DS101")

    assert "test_new.py" in output
    assert "test_old.py" not in output


def test_try_leaves_the_projects_files_as_they_were_after_a_failing_run(
    try_checks, tmp_path, write_test_file, watch
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\ndrill_sergeant_voice = false\n"
    )
    written = watch(tmp_path)

    code, _ = try_checks(".", "DS101")

    assert code == 1
    assert outside_cache(written()) == []


def test_try_removes_its_config_when_the_run_is_interrupted(
    try_checks, try_checks_script, tmp_path, write_test_file, watch, monkeypatch
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    seen = []

    def interrupted(args, prog_name):
        seen.append(tmp_path / args[args.index("--config") + 1])
        assert seen[0].is_file()
        raise KeyboardInterrupt

    monkeypatch.setattr(try_checks_script, "app", interrupted)
    written = watch(tmp_path)

    with pytest.raises(KeyboardInterrupt):
        try_checks(".", "DS101")

    assert seen and not seen[0].exists()
    assert outside_cache(written()) == []


def test_try_removes_its_config_when_the_run_refuses(
    try_checks, tmp_path, write_test_file, watch
):
    write_test_file(ASSERTION_FREE)
    written = watch(tmp_path)

    code, _ = try_checks(".", "DS999")

    assert code == 2
    assert outside_cache(written()) == []


def test_try_copies_text_beyond_ascii_from_the_projects_config(
    try_checks, tmp_path, write_test_file
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\nmarkers = ["slow: \U0001f422 tests"]\n',
        encoding="utf-8",
    )

    code, output = try_checks(".", "DS101")

    assert code == 1, output
    assert "DS101" in output


def test_try_refuses_a_config_that_does_not_parse(
    try_checks, tmp_path, write_test_file
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options\n")

    code, _ = try_checks(".", "DS101")

    assert code == 2


def test_try_turns_a_family_on_over_the_projects_own_entry(
    try_checks, tmp_path, write_test_file
):
    write_test_file(ASSERTION_FREE)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ndrill_sergeant_levels = ["DS101=off"]\n'
    )

    _, output = try_checks(".", "DS1xx")

    assert "DS101" in output
