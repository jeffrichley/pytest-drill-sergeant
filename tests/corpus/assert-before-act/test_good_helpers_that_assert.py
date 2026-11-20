"""Near-misses: what runs after the guard assertion is a helper that asserts, so it is
an assertion, not an act; and a helper `def` nested in the test asserts where it is
called, not where it is defined. Modelled on networkx's `check_independent`, pandas'
`self._run_test` and the `compare` nested in `test_class_ops`, and home-assistant's
`_assert_nothing_received`. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def _check_independent(graph, nodes):
    assert all(not graph.has_edge(u, v) for u in nodes for v in nodes)


def _assert_nothing_received(client):
    _check_inbox(client, [])


def _check_inbox(client, expected):
    assert client.inbox == expected


def test_guard_then_a_helper_that_asserts(graph):
    assert graph.frozen
    _check_independent(graph, {1, 3})


async def test_act_then_a_helper_two_calls_down(client):
    await client.subscribe("topic")
    _assert_nothing_received(client)


class TestCoercion:
    def _run_test(self, frame, expected):
        assert frame.dtype == expected

    def test_guard_then_a_method_that_asserts(self, frame):
        assert frame.size == 3
        self._run_test(frame, "int64")


def test_nested_helper_defined_first_called_after_the_act(clock):
    def compare(expected):
        assert clock.now() == expected

    assert clock.ticks == 0
    clock.tick()
    compare(1)
