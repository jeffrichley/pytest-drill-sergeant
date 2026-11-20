"""Assertions about values the test wrote itself, never passed through code.
The first is the catalog's example; the second is the Hacker News `a = 1`.
Analysed, never run."""

from shop import load_config


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
