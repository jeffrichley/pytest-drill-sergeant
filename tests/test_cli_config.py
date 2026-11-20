import pytest

pytestmark = pytest.mark.integration


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


def test_per_file_ignore_globs_are_relative_to_the_config_file(
    cli, tmp_path, unit_mark
):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "test_old.py").write_text("def test_old():\n    run()\n" + unit_mark)
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
        "drill_sergeant_source_dirs = nowhere",
    ],
    ids=[
        "unknown-key",
        "unknown-code",
        "bad-level",
        "non-numeric-threshold",
        "missing-source-dir",
    ],
)
def test_check_refuses_bad_config(cli, tmp_path, assertion_free_test, ini):
    (tmp_path / "pytest.ini").write_text(f"[pytest]\n{ini}\n")

    assert cli("check", "test_it.py").exit_code == 2


@pytest.mark.parametrize(
    "option",
    [("--config", "nowhere.ini"), ("--mode", "off")],
    ids=["missing-config-file", "no-flag-configures-drill-sergeant"],
)
def test_check_refuses_a_bad_option(cli, assertion_free_test, option):
    assert cli("check", *option, "test_it.py").exit_code == 2


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
