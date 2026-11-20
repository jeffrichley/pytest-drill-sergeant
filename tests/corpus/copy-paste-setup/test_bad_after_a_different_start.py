"""The pasted block starts after a line each test writes differently, and runs in
four tests, in a class and at module level. Analysed, never run."""

import pytest
from inventory import Shelf, Stock, Warehouse

pytestmark = pytest.mark.unit


class TestRestock:
    def test_restock_fills_the_shelf(self):
        sku = "A-1"
        warehouse = Warehouse(region="eu")  # expect: DS501
        warehouse.open()
        stock = Stock(warehouse)
        shelf = Shelf(stock, capacity=10)
        shelf.restock(sku)
        assert shelf.count(sku) == 10

    def test_restock_draws_down_the_stock(self):
        sku = "B-2"
        warehouse = Warehouse(region="eu")
        warehouse.open()
        stock = Stock(warehouse)
        shelf = Shelf(stock, capacity=10)
        shelf.restock(sku)
        assert stock.level(sku) == 90


def test_empty_shelf_reports_zero():
    warehouse = Warehouse(region="eu")
    warehouse.open()
    stock = Stock(warehouse)
    shelf = Shelf(stock, capacity=10)
    assert shelf.count("C-3") == 0


def test_shelf_refuses_past_capacity():
    sku = "D-4"
    warehouse = Warehouse(region="eu")
    warehouse.open()
    stock = Stock(warehouse)
    shelf = Shelf(stock, capacity=10)
    shelf.restock(sku)
    assert shelf.restock(sku) is False
