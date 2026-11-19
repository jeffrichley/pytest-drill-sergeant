"""Near-misses: tests that read data files, not source, and assert on their text.
Analysed, never run."""

import json
from pathlib import Path

from app import export

DATA = Path(__file__).parent / "data"


def test_export_writes_the_header(tmp_path):
    export(tmp_path / "out.csv")
    assert "name,email" in (tmp_path / "out.csv").read_text()


def test_fixture_file_has_ada():
    assert "Ada" in (DATA / "users.txt").read_text()


def test_config_parses():
    with open(DATA / "config.json") as handle:
        config = json.load(handle)
    assert "timeout" in config
