"""Near-misses: a skip inside a helper, a fixture or a `with` runs only when it is
reached. Analysed, never run.
"""

import shutil

import pytest
from archive import pack

pytestmark = pytest.mark.unit


def needs(tool):
    if shutil.which(tool) is None:
        pytest.skip(f"needs {tool}")


@pytest.fixture
def zstd():
    needs("zstd")
    return "zstd"


def test_pack_with_zstd(zstd):
    assert pack(["a.txt"], codec=zstd).endswith(".zst")


def test_pack_with_xz():
    needs("xz")
    assert pack(["a.txt"], codec="xz").endswith(".xz")
