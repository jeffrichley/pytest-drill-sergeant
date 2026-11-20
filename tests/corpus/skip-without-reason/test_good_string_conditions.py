"""Near-misses: a `skipif` or `xfail` on string conditions, or a hidden reason.

pytest shows a string condition as the reason (`condition: <the string>`), so
such a test has one. A `**kwargs` may hold a reason the file doesn't show.
Analysed, never run.
"""

import pytest
from graphs import Graph, shortest_path

pytestmark = pytest.mark.unit


@pytest.mark.skipif("not Graph.backends()")
def test_shortest_path_through_a_backend():
    assert shortest_path(Graph([(1, 2), (2, 3)]), 1, 3) == [1, 2, 3]


@pytest.mark.skipif("sys.platform == 'win32'", "sys.version_info < (3, 12)")
def test_shortest_path_on_a_large_graph():
    graph = Graph([(n, n + 1) for n in range(1000)])
    assert len(shortest_path(graph, 0, 999)) == 1000


@pytest.mark.skipif(condition="sys.platform == 'win32'")
def test_shortest_path_skips_a_removed_node():
    graph = Graph([(1, 2), (2, 3), (1, 3)]).without(2)
    assert shortest_path(graph, 1, 3) == [1, 3]


@pytest.mark.xfail("not Graph.supports_weights()")
def test_shortest_path_follows_the_lightest_edges():
    graph = Graph([(1, 2, 5), (2, 3, 5), (1, 3, 20)])
    assert shortest_path(graph, 1, 3, weighted=True) == [1, 2, 3]


SLOW = {"condition": "Graph.is_slow()", "reason": "pure-Python backend, see #4"}


@pytest.mark.skipif(**SLOW)
def test_shortest_path_on_a_complete_graph():
    graph = Graph.complete(50)
    assert len(shortest_path(graph, 0, 49)) == 2
