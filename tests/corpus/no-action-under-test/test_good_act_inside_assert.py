"""Near-misses: the action under test is a call inside the assertion itself.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def slugify(text):
    return text.lower().replace(" ", "-")


def test_slug_in_the_assert():
    assert slugify("Hello World") == "hello-world"


def test_raises_on_a_call():
    with pytest.raises(AttributeError, match="lower"):
        slugify(None)


async def test_awaited_value(client):
    assert await client.ping() == "pong"


def test_builtin_call_counts_as_an_action():
    assert len(slugify("a b")) == 3


def test_raises_in_call_form_calls_the_code():
    pytest.raises(AttributeError, slugify, None)
