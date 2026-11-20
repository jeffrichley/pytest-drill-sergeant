"""Reasonless skips that a string condition doesn't explain. Analysed, never run.

A `skipif` with one real condition beside a string, a blank string condition, or
an `xfail` that names what it raises still says nothing about why.
"""

import sys

import pytest
from graphs import Graph, shortest_path

pytestmark = pytest.mark.unit


@pytest.mark.skipif("not Graph.backends()", sys.platform == "win32")  # expect: DS401
def test_shortest_path_through_a_backend():
    assert shortest_path(Graph([(1, 2), (2, 3)]), 1, 3) == [1, 2, 3]


@pytest.mark.skipif("  ")  # expect: DS401
def test_shortest_path_to_itself():
    assert shortest_path(Graph([(1, 2)]), 1, 1) == [1]


@pytest.mark.xfail(raises=KeyError)  # expect: DS401
def test_shortest_path_to_a_missing_node():
    assert shortest_path(Graph([(1, 2)]), 1, 9) == []


class TestShortestPath:
    def test_shortest_path_on_a_directed_graph(self):
        graph = Graph([(1, 2)], directed=True)
        if not graph.supports_direction():
            pytest.skip()  # expect: DS401
        assert shortest_path(graph, 2, 1) is None
