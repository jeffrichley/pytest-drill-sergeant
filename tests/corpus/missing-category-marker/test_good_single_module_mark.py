"""A single module `pytestmark`, set after the tests, marks them all.

Analysed, never run.
"""

import pytest
from toaster import Toaster


def test_toaster_pops_the_toast():
    toaster = Toaster()
    toaster.load("rye")
    assert toaster.pop() == "rye"


pytestmark = pytest.mark.unit
