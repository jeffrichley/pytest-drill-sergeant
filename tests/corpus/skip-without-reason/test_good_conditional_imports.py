"""Near-misses: `importorskip` explains itself, and a string condition with a reason.

Analysed, never run.
"""

import pytest
from frames import to_frame

pytestmark = pytest.mark.unit


def test_frame_from_numpy_array():
    numpy = pytest.importorskip("numpy")
    assert to_frame(numpy.zeros(2)).shape == (2, 1)


@pytest.mark.skipif("sys.platform == 'win32'", reason="fork is POSIX only")
def test_frame_builds_in_a_forked_worker():
    assert to_frame([1, 2], workers=2).shape == (2, 1)
