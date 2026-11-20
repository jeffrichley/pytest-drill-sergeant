"""Near-misses: cleanup, known from the imports, that tolerates the one specific error
it can meet, such as a file already gone. Analysed, never run."""

import os
import shutil

import pytest

pytestmark = pytest.mark.unit


def save(path, text):
    path.write_text(text)


def test_cleanup_tolerates_a_missing_file(tmp_path):
    path = tmp_path / "missing"
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    assert not path.exists()


def test_cleanup_in_a_finally_tolerates_missing_files(tmp_path):
    path = tmp_path / "out.txt"
    save(path, "done")
    try:
        assert path.read_text() == "done"
    finally:
        try:
            os.remove(path)
            shutil.rmtree(tmp_path / "cache")
        except (FileNotFoundError, NotADirectoryError):
            pass
