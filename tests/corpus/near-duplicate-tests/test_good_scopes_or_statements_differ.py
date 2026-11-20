"""Near-miss: tests alike but for their values in different classes, or at module
level and in a class, and tests with one statement more. Analysed, never run."""

from shop import Cart


def test_one_apple_costs_three():
    cart = Cart()
    cart.add("apple", quantity=1)
    assert cart.total() == 3


def test_two_pears_cost_eight_after_a_refresh():
    cart = Cart()
    cart.add("pear", quantity=2)
    cart.refresh()
    assert cart.total() == 8


class TestEuroCart:
    def test_one_plum_costs_five(self):
        cart = Cart()
        cart.add("plum", quantity=1)
        assert cart.total() == 5


class TestDollarCart:
    def test_one_fig_costs_six(self):
        cart = Cart()
        cart.add("fig", quantity=1)
        assert cart.total() == 6
