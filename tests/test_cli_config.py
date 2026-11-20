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


# A test whose only finding is from a check on by default: DS803 on line 4.
UNSEEDED_DRAW = "import random\n\ndef test_draw():\n    assert random.random() < 2\n"


@pytest.fixture
def pkg_under_warn(tmp_path):
    """`pkg/`, holding a test with an unseeded random draw (DS803, on by default),
    under a `pytest.ini` setting warn mode; returned so a test can put a config file
    beside the test."""
    deep = tmp_path / "pkg"
    deep.mkdir()
    (deep / "test_draw.py").write_text(UNSEEDED_DRAW)
    (tmp_path / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])
    return deep


@pytest.mark.parametrize("name", WARN_CONFIGS)
def test_check_reads_the_config_pytest_would(cli, tmp_path, unseeded_random_test, name):
    (tmp_path / name).write_text(WARN_CONFIGS[name])

    result = cli("check", "test_draw.py")

    assert result.exit_code == 0, result.output
    assert "DS803" in result.output


def test_check_reads_pytest_9_native_toml(cli, tmp_path, unseeded_random_test):
    (tmp_path / "pyproject.toml").write_text(
        '[tool.pytest]\ndrill_sergeant_mode = "warn"\n'
    )

    assert cli("check", "test_draw.py").exit_code == 0


def test_check_searches_upward_from_the_given_paths(cli, tmp_path):
    deep = tmp_path / "pkg" / "tests"
    deep.mkdir(parents=True)
    (deep / "test_draw.py").write_text(UNSEEDED_DRAW)
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
def test_check_passes_over_files_without_a_pytest_section(
    cli, pkg_under_warn, name, content
):
    (pkg_under_warn / name).write_text(content)

    assert cli("check", "pkg").exit_code == 0


def test_the_nearest_config_wins(cli, pkg_under_warn):
    (pkg_under_warn / "pytest.ini").write_text("[pytest]\n")

    assert cli("check", "pkg").exit_code == 1


@pytest.mark.parametrize("name", ["pytest.ini", "pytest.toml"])
def test_a_found_pytest_file_with_no_pytest_table_still_ends_the_search(
    cli, pkg_under_warn, name
):
    (pkg_under_warn / name).write_text("")

    assert cli("check", "pkg").exit_code == 1


def test_config_option_overrides_discovery(cli, tmp_path, unseeded_random_test):
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    (tmp_path / "ci").mkdir()
    (tmp_path / "ci" / "pytest.ini").write_text(WARN_CONFIGS["pytest.ini"])

    assert cli("check", "--config", "ci/pytest.ini", "test_draw.py").exit_code == 0


def test_config_option_reads_any_toml_as_pytest_reads_a_pyproject(
    cli, tmp_path, unseeded_random_test
):
    (tmp_path / "ci.toml").write_text(WARN_CONFIGS["pyproject.toml"])

    assert cli("check", "--config", "ci.toml", "test_draw.py").exit_code == 0


@pytest.mark.parametrize(
    ("name", "content"),
    [
        ("ci.toml", '[pytest]\ndrill_sergeant_mode = "warn"\n'),
        ("pyproject.toml", "[tool.ruff]\nline-length = 88\n"),
        ("ci.toml", 'tool = "pytest"\n'),
        ("pytest.toml", "[tool.pytest]\n"),
        ("ci.ini", "[tool:pytest]\ndrill_sergeant_mode = warn\n"),
        ("pytest.ini", ""),
        ("ci.cfg", "[pytest]\ndrill_sergeant_mode = warn\n"),
    ],
    ids=[
        "other-toml-pytest-table",
        "pyproject-no-tool-pytest",
        "tool-not-a-table",
        "pytest-toml-no-pytest-table",
        "ini-cfg-section",
        "empty-pytest-ini",
        "cfg-ini-section",
    ],
)
def test_config_option_refuses_a_file_with_no_pytest_table(
    cli, tmp_path, unseeded_random_test, name, content
):
    (tmp_path / name).write_text(content)

    assert cli("check", "--config", name, "test_draw.py").exit_code == 2


def test_per_file_ignore_globs_are_relative_to_the_config_file(
    cli, tmp_path, unit_mark
):
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "test_old.py").write_text(
        "import random\n\ndef test_old():\n    assert random.random() < 2\n" + unit_mark
    )
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\ndrill_sergeant_per_file_ignores =\n    legacy/*: DS803\n"
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
def test_check_refuses_bad_config(cli, tmp_path, unseeded_random_test, ini):
    (tmp_path / "pytest.ini").write_text(f"[pytest]\n{ini}\n")

    assert cli("check", "test_draw.py").exit_code == 2


@pytest.mark.parametrize(
    "option",
    [("--config", "nowhere.ini"), ("--mode", "off")],
    ids=["missing-config-file", "no-flag-configures-drill-sergeant"],
)
def test_check_refuses_a_bad_option(cli, unseeded_random_test, option):
    assert cli("check", *option, "test_draw.py").exit_code == 2


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
    cli, tmp_path, unseeded_random_test, name, content
):
    (tmp_path / name).write_text(content)

    assert cli("check", "test_draw.py").exit_code == 2


def test_no_environment_variable_configures_drill_sergeant(
    cli, unseeded_random_test, monkeypatch
):
    monkeypatch.setenv("DRILL_SERGEANT_MODE", "off")
    monkeypatch.setenv("drill_sergeant_mode", "off")

    assert cli("check", "test_draw.py").exit_code == 1
