"""Broad expectations tucked inside loops, async tests and beside a good one.
Analysed, never run."""

import pytest


def parse(text):
    return int(text)


async def fetch(url):
    raise ConnectionError(url)


@pytest.mark.parametrize("text", [None, [], {}])
def test_every_bad_input_raises(text):
    for _ in range(2):
        with pytest.raises(Exception):  # expect: DS701
            parse(text)


async def test_unreachable_host_raises():
    with pytest.raises(Exception):  # expect: DS701
        await fetch("http://nowhere")


def test_two_expectations_in_one_test():
    with pytest.raises(ValueError, match="invalid literal"):
        parse("x")
    with pytest.raises(BaseException):  # expect: DS701
        parse(None)
