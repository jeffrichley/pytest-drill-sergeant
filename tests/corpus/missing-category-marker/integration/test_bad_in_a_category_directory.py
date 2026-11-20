"""An unmarked test in a directory named for a category marker: the fix suggests
`@pytest.mark.integration`. Analysed, never run.
"""

from warehouse import Warehouse


def test_warehouse_ships_an_order():  # expect: DS901
    warehouse = Warehouse()
    warehouse.stock("bolt", 3)
    assert warehouse.ship("bolt", 2) == 1
