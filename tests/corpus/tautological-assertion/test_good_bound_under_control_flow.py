"""Near-misses: names that aren't values the test wrote itself, because control
flow, a call or a rebinding decides what they hold at the assert. Analysed, never
run."""

import pytest
from shop import generate_paths, load_config, render

pytestmark = pytest.mark.unit


def test_branch_ran_for_the_edge(view):
    # networkx `classes/tests/test_reportviews.py:331`: set only if the branch ran.
    for edge in view:
        if edge[:2] == (2, 3):
            checked = True
    assert len(view) == 4
    assert checked


def test_bound_in_a_loop(orders):
    for order in orders:
        order.close()
        last = 1
    assert last == 1


def test_bound_under_try():
    try:
        load_config("cfg.toml")
        loaded = True
    except OSError:
        pytest.fail("config missing")
    assert loaded


def test_bound_twice(flag):
    seen = False
    seen = True
    assert render(flag) == "on"
    assert seen


def test_index_map_filled_by_the_call(graph):
    # networkx `algorithms/tests/test_similarity.py:934`: the call fills the dict.
    index_map = {}
    path_gen = generate_paths(graph, 10, index_map=index_map)
    paths = list(path_gen)
    assert len(paths) == 10
    assert index_map == {0: {0, 1}}


def test_alias_whose_source_is_rebound(frame):
    # pandas `tests/frame/methods/test_info.py:237`: `result` is rebound after
    # `expected` takes its value.
    result = render(frame, max_cols=101)
    expected = result
    result = render(frame)
    assert result is expected
