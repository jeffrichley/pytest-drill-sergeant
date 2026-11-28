"""Tests whose second act only looks like building data: the receiver isn't a list,
dict or set the test built itself (a fixture, a value from a call, a name rebound to
something else, or a `list` the module rebinds), or the helper called doesn't
assert. Each is still an act, and each test has three act-then-assert cycles.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def list(items):  # noqa: A001 -- the module rebinds `list`, so it is no builtin.
    return items


def _load(store):
    store.load()


def test_append_on_a_fixture(store, queue):
    store.load()
    assert store.ready
    queue.append("job")  # expect: DS104
    assert store.pending == ["job"]
    store.flush()
    assert store.pending == []


def test_append_on_a_call_result(store):
    store.load()
    assert store.ready
    jobs = store.jobs()
    jobs.append("job")  # expect: DS104
    assert store.pending == ["job"]
    store.flush()
    assert store.pending == []


def test_name_rebound_to_something_else(store):
    jobs = []
    store.load()
    assert store.ready
    jobs = store.jobs()
    jobs.append("job")  # expect: DS104
    assert store.pending == ["job"]
    store.flush()
    assert store.pending == []


def test_list_the_module_rebinds(store):
    store.load()
    assert store.ready
    jobs = list(store.queue)
    jobs.append("job")  # expect: DS104
    assert store.pending == ["job"]
    store.flush()
    assert store.pending == []


def test_helper_that_only_acts(store):
    store.reset()
    assert not store.ready
    _load(store)  # expect: DS104
    assert store.ready
    store.reset()
    assert not store.ready


def test_name_rebound_by_a_loop(store, batches):
    jobs = []
    for jobs in batches:
        store.queue(jobs)
    assert store.ready
    jobs.append("job")  # expect: DS104
    assert store.pending == ["job"]
    store.flush()
    assert store.pending == []
