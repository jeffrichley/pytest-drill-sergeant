"""Assertions about values the test wrote itself, never passed through code.
The first is the catalog's example; the second is the Hacker News `a = 1`.
Analysed, never run."""

import pytest
from shop import generate_paths, load_config, open_session

pytestmark = pytest.mark.unit


def test_config_loads():
    expected = {"debug": True}
    config = expected
    load_config("cfg.toml")
    assert config == expected  # expect: DS202


def test_a_is_one():
    a = 1
    load_config("cfg.toml")
    assert a == 1  # expect: DS202


def test_arithmetic_still_works():
    load_config("cfg.toml")
    assert 2 + 2 == 4  # expect: DS202


def test_flag_set_by_the_test():
    loaded: bool = True
    load_config("cfg.toml")
    assert loaded  # expect: DS202


def test_flag_set_before_the_loop(view):
    # Near miss of networkx `test_reportviews.py:331`: bound before the loop, not
    # under it, so the loop never decides it.
    checked = True
    for edge in view:  # expect: DS107
        assert len(edge) == 3
    assert checked  # expect: DS202


def test_dict_no_call_fills(graph):
    # Near miss of networkx `test_similarity.py:934`: the call never takes the dict.
    index_map = {}
    paths = list(generate_paths(graph, 10))
    assert len(paths) == 10
    assert index_map == {}  # expect: DS202


def test_alias_bound_inside_a_with():
    # A `with` body always runs: it decides nothing.
    with open_session():
        expected = [1, 2]
    actual = expected
    assert actual == [1, 2]  # expect: DS202
