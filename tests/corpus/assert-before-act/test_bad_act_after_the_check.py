"""Tests whose last act runs after every assertion, so its outcome goes unchecked.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_register_then_rename(registry):
    registry.register("ada")
    assert registry.names() == ["ada"]
    registry.rename("ada", "grace")  # expect: DS103


def test_import_rows(importer, rows):
    assert importer.count() == 0
    for row in rows:  # expect: DS103
        importer.load(row)


def test_remove_after_the_check(cart):
    cart.add("apple")
    assert cart.items == ["apple"]
    cart.remove("apple")  # expect: DS103
