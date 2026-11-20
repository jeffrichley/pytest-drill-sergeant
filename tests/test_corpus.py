"""The corpus: every check proven through the engine, file by file.

A file in a check's folder is analysed alone, as a test file; one in its `source/`
subfolder alone, as production code. A file in another subfolder of a check's folder
is analysed with the files beside it, as one run, for checks that compare tests
across files; its expected findings are still its own.
"""

import re
from pathlib import Path

import pytest

from pytest_drill_sergeant.engine import Config, analyze

CORPUS = Path(__file__).parent / "corpus"
CORPUS_FILES = sorted(CORPUS.rglob("*.py"))
SOURCE_FILES = [p for p in CORPUS_FILES if p.parent.name == "source"]
TEST_FILES = [p for p in CORPUS_FILES if p.parent.name != "source"]
EXPECT = re.compile(r"#\s*expect:\s*(.+)$")


def expected_findings(path):
    expected = set()
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        match = EXPECT.search(line)
        if match:
            for code in match.group(1).split(","):
                expected.add((code.strip(), line_no))
    return expected


def analysed_with(path):
    """The files analysed in one run with a corpus file, itself included."""
    if path.parent.parent == CORPUS:
        return [path]
    return sorted(path.parent.glob("*.py"))


def analyze_corpus_file(path):
    """The findings of the run a corpus file is analysed in."""
    if path in SOURCE_FILES:
        return analyze([], Config(), sources=[path])
    return analyze(analysed_with(path), Config())


@pytest.mark.parametrize(
    "path", CORPUS_FILES, ids=[str(p.relative_to(CORPUS)) for p in CORPUS_FILES]
)
def test_corpus_file_yields_exactly_its_expected_findings(path):
    findings = analyze_corpus_file(path)

    assert {(f.code, f.line) for f in findings if f.file == path} == expected_findings(
        path
    )


def test_whole_corpus_as_one_run_yields_exactly_the_expected_findings():
    """No corpus file's tests duplicate another's, so a cross-file check finds in
    one run over the whole corpus (the golden report's run) only what each file
    expects."""
    findings = analyze(TEST_FILES, Config(), sources=SOURCE_FILES)

    assert {(f.file, f.code, f.line) for f in findings} == {
        (path, code, line)
        for path in CORPUS_FILES
        for code, line in expected_findings(path)
    }


@pytest.mark.parametrize(
    "path",
    [p for p in CORPUS_FILES if p.name.removeprefix("test_").startswith("good_")],
    ids=lambda p: str(p.relative_to(CORPUS)),
)
def test_good_corpus_file_declares_no_findings(path):
    assert expected_findings(path) == set()
