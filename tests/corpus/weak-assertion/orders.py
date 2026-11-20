"""Project code the weak-assertion corpus calls: what each function returns is
read from its definition, never from its name. Analysed, never run."""

STOCK = {"sku-1": 3}


def in_stock(sku) -> bool:
    return bool(STOCK.get(sku))


def overdue(order, today):
    if order.due is None:
        return False
    return order.due < today


def is_ready(order):
    return order.ready_at


def find_order(order_id):
    return {"id": order_id}


async def confirmed(order) -> bool:
    return order.state == "confirmed"


def has_lines(order) -> "bool":
    return bool(order.lines)


def lines(order) -> bool:
    yield from order.lines
