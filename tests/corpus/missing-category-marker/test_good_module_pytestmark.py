"""A module `pytestmark` list holding a category marker among other marks marks
every test, in classes too. Analysed, never run.
"""

import sys

import pytest
from kettle import Kettle

pytestmark = [
    pytest.mark.skipif(sys.platform == "win32", reason="POSIX timers"),
    pytest.mark.integration,
]


def test_kettle_boils_water():
    kettle = Kettle()
    kettle.fill(1)
    assert kettle.boil() == 100


class TestKettle:
    def test_kettle_switches_off_when_boiled(self):
        kettle = Kettle()
        kettle.fill(1)
        kettle.boil()
        assert not kettle.is_on()
