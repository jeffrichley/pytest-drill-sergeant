"""Near-misses: the same call made twice, each result bound to its own name, then
compared: a test that the code gives the same answer every time. Analysed, never
run."""

from shop import serializer, slugify


def test_slugify_gives_the_same_slug_every_time():
    first = slugify("Hello World")
    second = slugify("Hello World")
    assert first == second


def test_dump_is_stable(order):
    once = serializer.dump(order)
    again = serializer.dump(order)
    assert once == again
