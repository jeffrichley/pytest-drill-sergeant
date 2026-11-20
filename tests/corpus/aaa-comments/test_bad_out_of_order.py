"""AAA comments out of order or repeated, and Arrange below the code it should
head. The markers follow a dash, which an AAA comment may carry. Analysed, never
run."""

import pytest

pytestmark = pytest.mark.unit


def test_checkout_total(basket):
    # Act
    total = basket.checkout()
    # Arrange - # expect: DS108
    basket.add("pear")
    # Assert
    assert total == 0


def test_discount_code(basket):
    # Arrange
    basket.add("plum")
    # Act
    basket.apply_code("SAVE10")
    # Assert
    assert basket.discount == 10
    # Act - # expect: DS108
    basket.remove_code()  # expect: DS104
    # Assert - # expect: DS108
    assert basket.discount == 0


def test_empty_after_clear(basket):
    basket.add("fig")
    # Arrange - # expect: DS108
    basket.add("kiwi")
    # Act
    basket.clear()
    # Assert
    assert basket.size() == 0
