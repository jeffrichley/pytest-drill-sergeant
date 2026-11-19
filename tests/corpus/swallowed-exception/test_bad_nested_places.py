"""Swallowed exceptions in classes, async tests, nested `try`s and `except*`.
Analysed, never run."""

import contextlib


async def fetch(url):
    raise ConnectionError(url)


class TestClient:
    def test_get_ignores_timeouts(self):
        try:
            fetch("http://example.com")
        except TimeoutError:  # expect: DS702
            pass
        assert fetch is not None


async def test_fetch_ignores_connection_errors():
    try:
        await fetch("http://nowhere")
    except ConnectionError:  # expect: DS702
        pass
    assert fetch is not None


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
    with contextlib.suppress(RuntimeError):
        assert fetch("c")
    try:
        fetch("d")
    except* ConnectionError:  # expect: DS702
        pass
