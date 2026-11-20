"""Near-misses: a `skipif` whose conditions are strings, which pytest shows as its reason.

pytest skips such a test with `condition: <the string>` as the reason, so it is
not skipped without one. Analysed, never run.
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
