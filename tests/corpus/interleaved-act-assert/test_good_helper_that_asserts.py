"""Near-misses: a bare call between the assertions goes into a helper whose body
asserts, so it is an assertion, not a second act. Modelled on networkx's
`test_single_source_shortest_path` and its `validate_grid_path`. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def validate_grid_path(rows, cols, source, target, path):
    assert path[0] == source
    assert path[-1] == target
    assert len(path) <= rows * cols


def _check_cycle(path):
    validate_grid_path(1, len(path), path[0], path[-1], path)


class TestShortestPath:
    def test_single_source_shortest_path(self, grid, cycle, nx):
        p = nx.shortest_path(cycle, 0)
        assert p[3] == [0, 1, 2, 3]
        p = nx.shortest_path(grid, 1)
        validate_grid_path(4, 4, 1, 12, p[12])
        p = nx.shortest_path(cycle, 0, weight="weight")
        assert p[3] == [0, 1, 2, 3]
        p = nx.shortest_path(grid, 1, weight="weight")
        validate_grid_path(4, 4, 1, 12, p[12])
        _check_cycle(p[3])
        assert p == nx.single_source_dijkstra_path(grid, 1)
