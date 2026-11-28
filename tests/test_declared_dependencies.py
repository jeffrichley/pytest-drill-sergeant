"""What the project declares: a `mocker` parameter is pytest-mock's fixture only when
the project names pytest-mock among its dependencies, and no fixture of that name the
test sees overrides it."""

import pytest

from pytest_drill_sergeant.engine import Config, analyze, inspect

pytestmark = pytest.mark.unit

DS301_ON_THE_TEST = [("DS301", 1)]

DECLARATIONS = {
    "project dependencies": (
        "pyproject.toml",
        '[project]\nname = "shop"\ndependencies = ["pytest-mock>=3"]\n',
    ),
    "optional dependencies": (
        "pyproject.toml",
        '[project.optional-dependencies]\ntest = ["pytest", "pytest-mock"]\n',
    ),
    "dependency group": (
        "pyproject.toml",
        '[dependency-groups]\ndev = [{include-group = "test"}]\ntest = ["pytest-mock"]\n',
    ),
    "uv dev dependencies": (
        "pyproject.toml",
        '[tool.uv]\ndev-dependencies = ["pytest-mock==3.14.0"]\n',
    ),
    "poetry dependencies": (
        "pyproject.toml",
        '[tool.poetry.dependencies]\npython = "^3.11"\npytest-mock = "^3"\n',
    ),
    "poetry dev dependencies": (
        "pyproject.toml",
        '[tool.poetry.dev-dependencies]\npytest-mock = "^3"\n',
    ),
    "poetry group": (
        "pyproject.toml",
        '[tool.poetry.group.test.dependencies]\npytest-mock = { version = "^3" }\n',
    ),
    "requirements.txt": ("requirements.txt", "pytest\npytest-mock\n"),
    "requirements_test.txt": (
        "requirements_test.txt",
        "-r requirements.txt\npytest-mock==3.14.0  # pinned\n",
    ),
    "requirements/test.txt": ("requirements/test.txt", "pytest-mock>=3.10\n"),
    "a spelling PEP 503 normalises": (
        "requirements-dev.txt",
        "Pytest_Mock[extra] ; python_version >= '3.11'\n",
    ),
    "tests/requirements.txt": ("tests/requirements.txt", "pytest-mock\n"),
}

NOT_DECLARATIONS = {
    "another package": ("requirements.txt", "pytest-mock-resources\npytest-mockito\n"),
    "a commented-out line": ("requirements.txt", "# pytest-mock\n"),
    "an option line": ("requirements.txt", "--find-links pytest-mock\n"),
    "a project that doesn't parse": (
        "pyproject.toml",
        '[project\ndependencies = ["pytest-mock"]\n',
    ),
    "a table pyproject.toml doesn't define": (
        "pyproject.toml",
        '[tool.other]\ndependencies = ["pytest-mock"]\n',
    ),
    "a text file not named requirements": ("constraints.txt", "pytest-mock\n"),
}


def declare(root, where, text):
    path = root / where
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.mark.parametrize(
    ("where", "text"), DECLARATIONS.values(), ids=list(DECLARATIONS)
)
def test_mocker_is_pytest_mocks_fixture_when_the_project_declares_it(
    mocker_test, tmp_path, where, text
):
    declare(tmp_path, where, text)

    findings = analyze([mocker_test], Config(root=tmp_path))

    assert [(f.code, f.line) for f in findings] == DS301_ON_THE_TEST


@pytest.mark.parametrize(
    ("where", "text"), NOT_DECLARATIONS.values(), ids=list(NOT_DECLARATIONS)
)
def test_mocker_is_not_a_mock_without_a_declaration(mocker_test, tmp_path, where, text):
    declare(tmp_path, where, text)

    assert analyze([mocker_test], Config(root=tmp_path)) == []


def test_mocker_is_not_a_mock_with_no_declaration_file_at_all(mocker_test, tmp_path):
    assert analyze([mocker_test], Config(root=tmp_path)) == []


def test_a_declaration_above_the_config_root_is_another_projects(mocker_test, tmp_path):
    declare(tmp_path, "requirements.txt", "pytest-mock\n")

    assert analyze([mocker_test], Config(root=tmp_path / "tests")) == []


def test_a_declaration_beside_the_tests_directory_is_not_on_its_way_up(
    mocker_test, tmp_path
):
    declare(tmp_path, "docs/requirements.txt", "pytest-mock\n")

    assert analyze([mocker_test], Config(root=tmp_path)) == []


def test_a_declaration_added_since_a_cached_run_is_seen(
    mocker_test, tmp_path, cache_dir
):
    inspect([mocker_test], Config(root=tmp_path), cache_dir=cache_dir)
    declare(tmp_path, "requirements.txt", "pytest-mock\n")

    findings = inspect(
        [mocker_test], Config(root=tmp_path), cache_dir=cache_dir
    ).findings

    assert [(f.code, f.line) for f in findings] == DS301_ON_THE_TEST


def test_a_conftest_mocker_fixture_added_since_a_cached_run_is_seen(
    mocker_test, tmp_path, cache_dir
):
    declare(tmp_path, "requirements.txt", "pytest-mock\n")
    inspect([mocker_test], Config(root=tmp_path), cache_dir=cache_dir)
    declare(
        tmp_path,
        "conftest.py",
        "import pytest\n\n@pytest.fixture\ndef mocker():\n    return object()\n",
    )

    findings = inspect(
        [mocker_test], Config(root=tmp_path), cache_dir=cache_dir
    ).findings

    assert findings == []


def test_an_imported_mocker_is_the_tests_own_fixture(mocker_test, tmp_path):
    declare(tmp_path, "requirements.txt", "pytest-mock\n")
    declare(tmp_path, "tests/conftest.py", "from shop.testing import mocker\n")

    assert analyze([mocker_test], Config(root=tmp_path)) == []


MOCKER_TEST = (
    "def test_it(mocker):\n"
    "    send = mocker.patch('shop.send', autospec=True)\n"
    "    run()\n"
    "    assert send.called\n"
)
DECLARING_CONFIG = (
    '[project]\nname = "shop"\ndependencies = ["pytest-mock"]\n'
    "[tool.pytest.ini_options]\n"
)


@pytest.mark.integration
def test_cli_reads_the_declaration_beside_its_config(cli, tmp_path, unit_mark):
    (tmp_path / "pyproject.toml").write_text(DECLARING_CONFIG)
    (tmp_path / "test_it.py").write_text(MOCKER_TEST + unit_mark)

    assert "test_it.py:1: DS301" in cli("check", "test_it.py").output


@pytest.mark.integration
def test_plugin_reads_the_declaration_beside_its_config(drill, pytester, unit_mark):
    pytester.makepyprojecttoml(DECLARING_CONFIG)
    pytester.makepyfile(test_it=MOCKER_TEST + unit_mark)

    assert "test_it.py:1: DS301" in drill().stdout.str()
