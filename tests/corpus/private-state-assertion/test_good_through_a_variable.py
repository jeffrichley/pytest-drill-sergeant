"""Near-misses: a private read held in a local variable that never reaches an
assertion, or a name also bound from public state. Analysed, never run."""

import pytest
from app import Driver

pytestmark = pytest.mark.unit


def test_a_private_read_used_only_to_act(tmp_path):
    driver = Driver(tmp_path)
    opts = driver._options()
    result = driver.run(opts)
    assert result.ok


def test_a_private_read_handed_to_the_act_as_an_argument(tmp_path):
    driver = Driver(tmp_path)
    result = driver.run(driver._options())
    assert result.ok


def test_a_name_rebound_from_public_state():
    driver = Driver("dee")
    opts = driver._options()
    driver.configure(opts)
    opts = driver.options()
    assert opts.model is None


def test_a_parameter_rebound_from_private_state(opts):
    driver = Driver("dee")
    if opts is None:
        opts = driver._options()
    assert opts.model is None


class TestDriver:
    def setup_method(self):
        self._driver = Driver("dee")

    def test_own_instance_held_in_a_variable(self):
        driver = self._driver
        driver.start()
        assert driver.started
