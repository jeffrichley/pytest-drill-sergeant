"""Swallowed exceptions in classes, async tests, nested `try`s and `except*`.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


async def fetch(url):
    raise ConnectionError(url)


class TestClient:
    def test_get_ignores_timeouts(self):
        try:
            fetch("http://example.com")
        except TimeoutError:  # expect: DS702
            pass
        assert fetch is not None  # expect: DS201


async def test_fetch_ignores_connection_errors():
    try:
        await fetch("http://nowhere")
    except ConnectionError:  # expect: DS702
        pass
    assert fetch is not None  # expect: DS201


def test_nested_try_inner_swallowed():
    try:
        try:
            fetch("a")
        except ValueError:  # expect: DS702
            pass
        assert fetch("b")
    except KeyError:
        raise


def test_exception_group_swallowed():
    try:
        fetch("d")
    except* ConnectionError:  # expect: DS702
        pass


def test_cleanup_swallows_every_error(tmp_path):
    path = tmp_path / "missing"
    try:
        path.unlink()
    except Exception:  # expect: DS702
        pass
    assert not path.exists()


def test_method_named_like_cleanup_swallows_an_error(tmp_path):
    path = tmp_path / "missing"
    try:
        path.unlink()
    except FileNotFoundError:  # expect: DS702
        pass
    assert not path.exists()


def test_act_swallows_a_specific_error(tmp_path):
    try:
        fetch("http://example.com")
    except ConnectionError:  # expect: DS702
        pass
    assert tmp_path.exists()
