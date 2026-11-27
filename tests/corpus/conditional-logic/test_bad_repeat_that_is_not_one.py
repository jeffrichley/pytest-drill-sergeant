"""Loops over `range` that are not a plain repeat: the near-misses of
test_good_deliberate_repeat.py. One reads its target, so each pass checks something
different; one carries state from pass to pass; and two `range` calls aren't a
positive count written out. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_reads_its_target(client):
    for n in range(3):  # expect: DS107
        assert client.page(n).number == n


def test_carries_a_total(client):
    total = 0
    for _ in range(3):  # expect: DS107
        total += client.next_value()
        assert total > 0


def test_zero_times(client):
    for _ in range(0):  # expect: DS107
        assert client.connected


def test_count_from_a_fixture(client, count):
    for _ in range(count):  # expect: DS107
        assert client.connected
