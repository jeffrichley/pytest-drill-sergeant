"""Near-misses: a loop that repeats the act a fixed number of times on purpose,
never reading its target, so every pass checks the same outcome. Modelled on
home-assistant's zwave_js `test_unique_id_migration`, which re-adds a node twice to
prove the second time changes nothing. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


async def test_re_adding_a_node_changes_nothing(driver, registry, node):
    for _ in range(2):
        driver.emit("node added", node)
        entry = registry.get("sensor.power")
        assert entry.unique_id == "3245146787.32-50-0-value-66049"


def test_reconnecting_three_times(client):
    for attempt in range(3):
        client.reconnect()
        assert client.connected


def test_settling_twice_leaves_the_same_total(cart):
    for _ in range(2):

        def settle():
            return cart.settle()

        total: int = settle()
        assert total == 6
        assert (count := cart.count) == 3, count
