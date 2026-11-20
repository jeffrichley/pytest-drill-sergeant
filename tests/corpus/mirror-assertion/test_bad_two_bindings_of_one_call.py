"""The same call bound to two names, then compared: whatever the names say, the
expected side comes from the code under test. Analysed, never run."""

from shop import serializer, slugify


def test_slugify_gives_the_same_slug_every_time():
    first = slugify("Hello World")
    second = slugify("Hello World")
    assert first == second  # expect: DS203


def test_dump_is_stable(order):
    once = serializer.dump(order)
    again = serializer.dump(order)
    assert once == again  # expect: DS203
