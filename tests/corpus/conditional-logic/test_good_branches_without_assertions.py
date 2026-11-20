"""Near-misses: branches that hold no assertion (a skip, conditional setup), and an
`if` that is itself the assertion. Analysed, never run."""

import shutil
import sys

import pytest

pytestmark = pytest.mark.unit


def test_git_status(repo):
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    assert repo.status() == "clean"


def test_line_endings(writer, tmp_path):
    expected = b"a\r\nb\r\n" if sys.platform == "win32" else b"a\nb\n"
    path = tmp_path / "out.txt"
    if not path.parent.exists():
        path.parent.mkdir()

    writer.write(path, ["a", "b"])

    assert path.read_bytes() == expected


def test_total_with_a_message(cart):
    cart.add("apple", price=3)
    if cart.total != 3:
        pytest.fail(f"total was {cart.total}, cart held {cart.items}")


def test_status_with_a_message(service):
    status = service.ping()
    if status != "up":
        raise AssertionError(f"service reported {status}")
