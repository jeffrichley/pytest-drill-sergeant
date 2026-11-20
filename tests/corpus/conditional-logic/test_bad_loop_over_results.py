"""Assertions inside loops over what the code returns or a fixture hands in: an
empty result checks nothing and passes. `ROWS` is bound twice, so the file never
settles its values and no `parametrize` is suggested. One test came from
unseeded-random's near-misses, and still is one: a loop variable named `random`
isn't the module (DS803). Analysed, never run."""

import random  # noqa: F401 -- the module the loop variable shadows

ROWS = [{"id": 1}]
ROWS = [{"id": 1}, {"id": 2}]


def test_loop_variable_named_random(rngs):
    for random in rngs:  # noqa: F402 -- the shadowing is the near-miss  # expect: DS107
        assert random.choice(["apple"]) == "apple"


def test_every_user_is_active(client):
    response = client.get("/users?active=1")
    for user in response.json():  # expect: DS107
        assert user["active"] is True


def test_rows_import(importer):
    importer.load(ROWS)
    for row in importer.rows():  # expect: DS107
        assert row.valid


def test_drain_the_queue(queue):
    queue.put_many([1, 2, 3])
    while queue:  # expect: DS107
        item = queue.pop()
        assert item in {1, 2, 3}


async def test_stream_yields_only_ticks(feed):
    async for event in feed.stream(limit=10):  # expect: DS107
        assert event.kind == "tick"


def test_checks_in_a_helper(catalog):
    def check_all(items):
        for item in items:  # expect: DS107
            assert item.price > 0

    check_all(catalog.items())
