"""Seeded from the archived rewrite's coverage-padding tests (tag
archive/2026-02-13/rewrite/main, tests/unit/test_ultimate_coverage.py): every
assertion holds for any module that imports.

Analysed, never run.
"""

import pytest_drill_sergeant.core

import pytest_drill_sergeant.plugin


def test_scoring_models_import():  # expect: DS102
    """Test importing scoring_models to ensure coverage."""
    assert pytest_drill_sergeant.core.scoring_models is not None  # expect: DS201


def test_core_init_import():  # expect: DS102
    """Test importing core __init__ to ensure coverage."""
    assert pytest_drill_sergeant.core is not None  # expect: DS201


def test_plugin_init_import():  # expect: DS102
    """Not None, written the long way round."""
    assert pytest_drill_sergeant.plugin != None  # noqa: E711  # expect: DS201


async def test_async_import():
    plugin = await pytest_drill_sergeant.plugin.load()
    assert plugin  # expect: DS201
