"""An agent "making the test not crash": the error caught and dropped. Analysed,
never run."""

import logging

import pytest

pytestmark = pytest.mark.unit


def sync_all():
    raise RuntimeError("sync broke")


def test_sync():
    try:
        sync_all()
    except Exception:  # expect: DS702
        pass
    assert True


def test_sync_each_source():
    for source in ["a", "b"]:  # expect: DS107
        try:
            sync_all()
            assert source  # expect: DS201
        except RuntimeError:  # expect: DS702
            continue


def test_sync_returns_early():
    try:
        sync_all()
    except RuntimeError:  # expect: DS702
        return
    assert sync_all() is None


def test_sync_logs_and_moves_on():
    try:
        result = sync_all()
    except Exception as error:  # expect: DS702
        logging.warning("sync failed: %s", error)
        result = None
    assert result is None


def test_sync_bare_except():
    try:
        sync_all()
    # The bare `except` is the case under test.
    except:  # noqa: E722  # expect: DS702
        ...
