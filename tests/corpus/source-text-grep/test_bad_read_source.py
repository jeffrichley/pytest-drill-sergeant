"""Tests that read a `.py` file and assert on its text. Seeded from the
failure-modes catalog (#23). Analysed, never run."""

from pathlib import Path


def test_retry_enabled():
    assert "retry=True" in Path("src/client.py").read_text()  # expect: DS603


def test_debug_off():
    source = open("src/app/config.py").read()
    assert "DEBUG = False" in source  # expect: DS603


def test_os_import_removed():
    with open("src/app/paths.py") as handle:
        text = handle.read()
    assert "import os" not in text  # expect: DS603


def test_source_lines_through_a_path(root):
    lines = (root / "src" / "app" / "jobs.py").read_text().splitlines()
    assert "def run_job(job):" in lines  # expect: DS603
