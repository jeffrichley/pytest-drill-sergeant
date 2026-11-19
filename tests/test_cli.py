import shutil
from pathlib import Path

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


def test_check_refuses_a_missing_path(cli):
    assert cli("check", "nowhere").exit_code == 2


def test_check_refuses_a_file_that_does_not_parse(cli, tmp_path):
    (tmp_path / "test_broken.py").write_text("def test_broken(:\n")

    assert cli("check", "test_broken.py").exit_code == 2


# A change to the report changes golden/check.txt: rerun `drill-sergeant check suite`
# over a copy of the corpus with NO_COLOR=1 COLUMNS=100, and review the diff.
def test_check_output_matches_the_golden_report(cli, tmp_path):
    golden = Path(__file__).parent / "golden" / "check.txt"
    suite = tmp_path / "suite"
    shutil.copytree(CORPUS, suite)

    result = cli("check", "suite")

    assert result.output == golden.read_text()
