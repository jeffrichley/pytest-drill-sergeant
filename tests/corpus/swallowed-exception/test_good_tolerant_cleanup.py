"""Near-misses: cleanup, known from the imports, that tolerates the one specific error
it can meet, such as a file already gone. Analysed, never run."""

import os
import shutil


def save(path, text):
    path.write_text(text)


def test_cleanup_tolerates_a_missing_file(tmp_path):
    path = tmp_path / "missing"
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass
    assert not path.exists()


def test_cleanup_after_the_check_tolerates_missing_files(tmp_path):
    path = tmp_path / "out.txt"
    save(path, "done")
    assert path.read_text() == "done"
    try:
        os.remove(path)
        shutil.rmtree(tmp_path / "cache")
    except (FileNotFoundError, NotADirectoryError):
        pass
