"""Assertions on a module's private globals and loaded flags. Analysed, never run."""

import pytest
from app import config, registry

pytestmark = pytest.mark.unit


def test_registry_starts_empty():
    assert registry._registry == {}  # expect: DS602


def test_config_loaded():
    config.load()
    assert config._loaded is True  # expect: DS602


def test_private_state_in_a_nested_block(items):
    for item in items:  # expect: DS107
        if item.ready:
            assert not item._dirty  # expect: DS602
