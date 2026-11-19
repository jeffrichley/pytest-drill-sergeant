"""Swallowed exceptions in classes, async tests, nested `try`s and `except*`.
Analysed, never run."""


async def fetch(url):
    raise ConnectionError(url)


class TestClient:
    def test_get_ignores_timeouts(self):  # expect: DS201
        try:
            fetch("http://example.com")
        except TimeoutError:  # expect: DS702
            pass
        assert fetch is not None


async def test_fetch_ignores_connection_errors():  # expect: DS201
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


def test_exception_group_swallowed():  # expect: DS101
    try:
        fetch("d")
    except* ConnectionError:  # expect: DS702
        pass
