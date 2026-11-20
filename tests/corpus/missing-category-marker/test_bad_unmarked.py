"""Tests with no mark at all, or only marks that are no category marker.

Analysed, never run.
"""

import pytest
from shelf import Shelf


def test_shelf_starts_empty():  # expect: DS901
    assert Shelf().books() == []


@pytest.mark.slow
def test_shelf_holds_a_thousand_books():  # expect: DS901
    shelf = Shelf(capacity=1000)
    shelf.fill("dune")
    assert len(shelf.books()) == 1000


@pytest.mark.parametrize("title", ["dune", "emma"])
@pytest.mark.timeout(5)
def test_shelf_finds_a_book_by_title(title):  # expect: DS901
    shelf = Shelf()
    shelf.add(title)
    assert shelf.find(title) == title


async def test_shelf_lends_a_book_async():  # expect: DS901
    shelf = Shelf()
    shelf.add("ulysses")
    assert await shelf.lend("ulysses") == "ulysses"
