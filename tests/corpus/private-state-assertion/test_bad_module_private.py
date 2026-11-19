"""Assertions on a module's private globals and loaded flags. Analysed, never run."""

from app import config, registry


def test_registry_starts_empty():  # expect: DS102
    assert registry._registry == {}  # expect: DS602


def test_config_loaded():
    config.load()
    assert config._loaded is True  # expect: DS602


def test_private_state_in_a_nested_block(items):
    for item in items:
        if item.ready:
            assert not item._dirty  # expect: DS602
