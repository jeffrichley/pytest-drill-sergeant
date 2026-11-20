"""Cleanup after the last assertion: it never runs when an assertion fails, so it
belongs in a fixture or a `finally`. Known cleanup through the imports is no
different. Analysed, never run."""

import os
import shutil

import pytest

pytestmark = pytest.mark.unit


def test_writes_report(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    path.unlink()  # expect: DS103


def test_files_removed_after(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    os.remove(path)  # expect: DS103
    os.unlink(tmp_path / "lock")
    shutil.rmtree(tmp_path / "cache")
