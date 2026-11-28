"""Near-misses: what runs between the assertions only builds data the test made
itself, a list, dict or set from a literal, a comprehension or the builtin `list()`,
`dict()` or `set()`, so it is no act. Counted as acts, each test would have three or
more act-then-assert cycles. Modelled on pandas' `test_dt_accessor_api_for_categorical`
(`attr_names.append("freq")`). Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_list_built_from_the_builtin(ser, idx):
    cat = ser.astype("category")
    cat.cache()
    assert cat.dtype == "category"
    attr_names = list(ser.ops)
    if idx.is_datetime:
        attr_names.append("freq")
    assert cat.attrs >= set(attr_names)
    attr_names.append("tz")
    assert cat.attrs == set(attr_names)


def test_literals_and_comprehensions(store):
    store.load()
    assert store.ready
    names = []
    names.append("a")
    seen = {}
    seen.update(a=1)
    assert store.match(names, seen)
    tags = {"x"}
    tags.add("y")
    squares = [n * n for n in range(3)]
    squares.extend([9])
    assert store.match(tags, squares)
    lookup = dict(a=1)
    lookup.setdefault("b", 2)
    assert store.match(lookup)
