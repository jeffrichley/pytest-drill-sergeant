"""Near-misses: the act is inside the assertion, so one `# Act and assert` heads
both, and a test with no setup needs no `# Arrange`. Analysed, never run."""

import pytest
from shop.pricing import apply_discount
from shop.text import slugify


def test_negative_amount_is_refused(wallet):
    # Arrange
    amount = -5
    # Act and assert
    with pytest.raises(ValueError, match="negative"):
        wallet.pay(amount)


def test_discount_applies():
    # Act & Assert
    assert apply_discount(price=100, rate=0.1) == 90


def test_slugify_strips_spaces():
    # act and assert: spaces become dashes
    assert slugify(" a b ") == "a-b"
