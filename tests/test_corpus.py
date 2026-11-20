"""The corpus: every check proven through the engine, file by file.

A file under a `source/` folder is production code, handed to the engine as such;
every other file is a test file.
"""

import re
from pathlib import Path

import pytest

from pytest_drill_sergeant.engine import Config, analyze

CORPUS = Path(__file__).parent / "corpus"
CORPUS_FILES = sorted(CORPUS.rglob("*.py"))
EXPECT = re.compile(r"#\s*expect:\s*(.+)$")


def expected_findings(path):
    expected = set()
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        match = EXPECT.search(line)
        if match:
            for code in match.group(1).split(","):
                expected.add((code.strip(), line_no))
    return expected


def analyze_corpus_file(path):
    """The findings for a corpus file, read as production code under `source/`."""
    if path.parent.name == "source":
        return analyze([], Config(), sources=[path])
    return analyze([path], Config())


@pytest.mark.parametrize(
    "path", CORPUS_FILES, ids=[str(p.relative_to(CORPUS)) for p in CORPUS_FILES]
)
def test_corpus_file_yields_exactly_its_expected_findings(path):
    findings = analyze_corpus_file(path)

    assert {(f.code, f.line) for f in findings} == expected_findings(path)


@pytest.mark.parametrize(
    "path",
    [p for p in CORPUS_FILES if p.name.removeprefix("test_").startswith("good_")],
    ids=lambda p: str(p.relative_to(CORPUS)),
)
def test_good_corpus_file_declares_no_findings(path):
    assert expected_findings(path) == set()
