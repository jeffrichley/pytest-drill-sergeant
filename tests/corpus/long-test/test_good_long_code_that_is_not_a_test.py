"""Near-misses: a long fixture, a long helper and a long method of a class pytest
doesn't collect are not tests, so their length is not a test's. Analysed, never
run."""

import pytest
from inventory import Warehouse


@pytest.fixture
def warehouse(tmp_path):
    store = Warehouse(root=tmp_path)
    store.add_bin("E1-01", capacity=100)
    store.add_bin("E1-02", capacity=100)
    store.add_bin("E1-03", capacity=100)
    store.add_bin("E2-01", capacity=50)
    store.add_bin("E2-02", capacity=50)
    store.add_bin("E2-03", capacity=50)
    store.add_bin("E3-01", capacity=25)
    store.add_bin("E3-02", capacity=25)
    store.add_bin("E3-03", capacity=25)
    store.add_product("A-100", weight=1.2)
    store.add_product("A-101", weight=0.8)
    store.add_product("A-102", weight=2.4)
    store.add_product("B-200", weight=5.0)
    store.add_product("B-201", weight=4.1)
    store.add_product("B-202", weight=3.3)
    store.add_product("C-300", weight=0.2)
    store.add_product("C-301", weight=0.3)
    store.add_product("C-302", weight=0.4)
    store.receive("A-100", qty=40, bin="E1-01")
    store.receive("A-101", qty=30, bin="E1-02")
    store.receive("A-102", qty=20, bin="E1-03")
    store.receive("B-200", qty=10, bin="E2-01")
    store.receive("B-201", qty=12, bin="E2-02")
    store.receive("B-202", qty=14, bin="E2-03")
    store.receive("C-300", qty=5, bin="E3-01")
    store.receive("C-301", qty=6, bin="E3-02")
    store.receive("C-302", qty=7, bin="E3-03")
    store.reserve("A-100", qty=4, order="o-1")
    store.reserve("A-101", qty=3, order="o-1")
    store.reserve("B-200", qty=1, order="o-2")
    store.reserve("B-201", qty=2, order="o-2")
    store.reserve("C-300", qty=1, order="o-3")
    store.reserve("C-301", qty=1, order="o-3")
    store.reserve("C-302", qty=1, order="o-3")
    store.set_policy(picking="fifo", replenish_at=5)
    store.set_hours(open_at="07:00", close_at="19:00")
    store.set_zone("E1", temperature="ambient")
    store.set_zone("E2", temperature="ambient")
    store.set_zone("E3", temperature="chilled")
    store.enable_audit()
    store.commit()
    return store


def build_manifest(store, order):
    lines = []
    for reservation in store.reservations(order=order):
        product = store.product(reservation.sku)
        lines.append(
            {
                "sku": reservation.sku,
                "qty": reservation.qty,
                "bin": reservation.bin,
                "weight": product.weight * reservation.qty,
            }
        )
    header = {
        "order": order,
        "lines": len(lines),
        "weight": sum(line["weight"] for line in lines),
    }
    footer = {
        "signed_by": None,
        "checked": False,
    }
    manifest = {
        "header": header,
        "lines": lines,
        "footer": footer,
    }
    for line in lines:
        line["label"] = f"{order}-{line['sku']}"
    for line in lines:
        line["zone"] = line["bin"][:2]
    for line in lines:
        line["chilled"] = line["zone"] == "E3"
    for line in lines:
        line["fragile"] = line["weight"] < 1
    if any(line["chilled"] for line in lines):
        manifest["header"]["cold_chain"] = True
    if any(line["fragile"] for line in lines):
        manifest["header"]["handle_with_care"] = True
    return manifest


class TestScenarioBuilder:
    """A helper class with `__init__`: pytest doesn't collect it."""

    def __init__(self, store):
        self.store = store

    def test_scenario(self):
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-100", qty=1, bin="E1-01")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("A-101", qty=1, bin="E1-02")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("B-200", qty=1, bin="E2-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.receive("C-300", qty=1, bin="E3-01")
        self.store.commit()
        self.store.audit()
        self.store.reconcile()
        self.store.report()
        self.store.close()
        self.store.reopen()
        self.store.commit()
        self.store.audit()
        self.store.reconcile()
        self.store.report()
        return self.store


def test_manifest_weighs_the_order(warehouse):
    manifest = build_manifest(warehouse, "o-1")

    assert manifest["header"]["weight"] == 7.2
