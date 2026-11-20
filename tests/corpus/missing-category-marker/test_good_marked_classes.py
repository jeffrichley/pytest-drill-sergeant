"""A category marker on a class, or in its `pytestmark`, marks its tests and the
tests of the classes inside it. Analysed, never run.
"""

import pytest
from lamp import Lamp


@pytest.mark.e2e
class TestLamp:
    def test_lamp_turns_on(self):
        lamp = Lamp()
        lamp.switch()
        assert lamp.is_lit()

    class TestDimmer:
        def test_dimmer_halves_the_light(self):
            lamp = Lamp(brightness=100)
            lamp.dim()
            assert lamp.brightness() == 50


class TestBulb:
    pytestmark = [pytest.mark.slow, pytest.mark.unit]

    def test_bulb_burns_out_after_its_hours(self):
        bulb = Lamp(bulb_hours=1).bulb
        bulb.burn(2)
        assert bulb.is_dead()
