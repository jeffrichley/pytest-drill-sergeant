"""Broad expectations tucked inside loops, async tests and beside a good one.
Analysed, never run."""

import pytest


def parse(text):
    return int(text)


async def fetch(url):
    raise ConnectionError(url)


@pytest.mark.parametrize("text", [None, [], {}])
def test_every_bad_input_raises(text):
    for _ in range(2):  # expect: DS107
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


def test_caught_exception_only_printed():
    with pytest.raises(Exception) as excinfo:  # expect: DS701
        parse("x")
    print(excinfo.value)
