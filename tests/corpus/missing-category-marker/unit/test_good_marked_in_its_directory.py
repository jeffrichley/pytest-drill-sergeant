"""A test in a directory named for a category marker, marked: the directory alone
would not have done. Analysed, never run.
"""

import pytest
from warehouse import Warehouse


@pytest.mark.unit
def test_warehouse_counts_its_stock():
    warehouse = Warehouse()
    warehouse.stock("nut", 4)
    assert warehouse.count("nut") == 4
