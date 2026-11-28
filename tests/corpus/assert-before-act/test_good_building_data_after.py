"""Near-misses: what runs after the last assertion only builds data the test made
itself, a list, dict or set from a literal, a comprehension or the builtin `list()`,
`dict()` or `set()`, so it is no unchecked act. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_collects_after_the_check(store):
    seen = []
    store.load()
    assert store.ready
    seen.append(store.name)


def test_fills_a_dict_after_the_check(store):
    lookup = dict(a=1)
    store.load()
    assert store.ready
    lookup.update(b=2)
