"""Literals holding a call are code, not data, so they still count line by line: an
async test in a class whose request payload builds each item with a call (53 lines
of code), and a test whose expected text is an f-string that calls (53). Analysed,
never run."""

import pytest

pytestmark = pytest.mark.unit


class TestImportApi:
    async def test_import_takes_a_batch(self, client, make_item):  # expect: DS105
        payload = {
            "batch_id": "b-2026-11-19",
            "source": "warehouse-east",
            "items": [
                make_item(sku="A-100", qty=4, bin="E1-01"),
                make_item(sku="A-101", qty=1, bin="E1-02"),
                make_item(sku="A-102", qty=9, bin="E1-03"),
                make_item(sku="B-200", qty=2, bin="E2-01"),
                make_item(sku="B-201", qty=7, bin="E2-02"),
                make_item(sku="B-202", qty=3, bin="E2-03"),
                make_item(sku="C-300", qty=5, bin="E3-01"),
                make_item(sku="C-301", qty=8, bin="E3-02"),
                make_item(sku="C-302", qty=6, bin="E3-03"),
                make_item(sku="D-400", qty=1, bin="E4-01"),
                make_item(sku="D-401", qty=2, bin="E4-02"),
                make_item(sku="D-402", qty=4, bin="E4-03"),
                make_item(sku="E-500", qty=3, bin="E5-01"),
                make_item(sku="E-501", qty=5, bin="E5-02"),
                make_item(sku="E-502", qty=2, bin="E5-03"),
                make_item(sku="F-600", qty=1, bin="E6-01"),
                make_item(sku="F-601", qty=4, bin="E6-02"),
                make_item(sku="F-602", qty=6, bin="E6-03"),
                make_item(sku="G-700", qty=2, bin="E7-01"),
                make_item(sku="G-701", qty=9, bin="E7-02"),
                make_item(sku="G-702", qty=1, bin="E7-03"),
                make_item(sku="H-800", qty=3, bin="E8-01"),
                make_item(sku="H-801", qty=7, bin="E8-02"),
                make_item(sku="H-802", qty=2, bin="E8-03"),
                make_item(sku="J-900", qty=5, bin="E9-01"),
                make_item(sku="J-901", qty=1, bin="E9-02"),
                make_item(sku="J-902", qty=8, bin="E9-03"),
                make_item(sku="K-110", qty=2, bin="F1-01"),
                make_item(sku="K-111", qty=3, bin="F1-02"),
                make_item(sku="K-112", qty=4, bin="F1-03"),
                make_item(sku="L-120", qty=1, bin="F2-01"),
                make_item(sku="L-121", qty=2, bin="F2-02"),
                make_item(sku="L-122", qty=3, bin="F2-03"),
            ],
            "carrier": "Northline",
            "priority": "normal",
        }

        response = await client.post("/imports", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["batch_id"] == "b-2026-11-19"
        assert body["accepted"] == 33
        assert body["rejected"] == 0
        assert body["total_qty"] == 118
        assert body["carrier"] == "Northline"
        assert body["source"] == "warehouse-east"
        assert body["priority"] == "normal"
        assert body["errors"] == []


def test_card_lays_out_a_node(node, render_card):  # expect: DS105
    expected = f"""
    | {node.name.upper()}
    | field_00: {node.field_00}
    | field_01: {node.field_01}
    | field_02: {node.field_02}
    | field_03: {node.field_03}
    | field_04: {node.field_04}
    | field_05: {node.field_05}
    | field_06: {node.field_06}
    | field_07: {node.field_07}
    | field_08: {node.field_08}
    | field_09: {node.field_09}
    | field_10: {node.field_10}
    | field_11: {node.field_11}
    | field_12: {node.field_12}
    | field_13: {node.field_13}
    | field_14: {node.field_14}
    | field_15: {node.field_15}
    | field_16: {node.field_16}
    | field_17: {node.field_17}
    | field_18: {node.field_18}
    | field_19: {node.field_19}
    | field_20: {node.field_20}
    | field_21: {node.field_21}
    | field_22: {node.field_22}
    | field_23: {node.field_23}
    | field_24: {node.field_24}
    | field_25: {node.field_25}
    | field_26: {node.field_26}
    | field_27: {node.field_27}
    | field_28: {node.field_28}
    | field_29: {node.field_29}
    | field_30: {node.field_30}
    | field_31: {node.field_31}
    | field_32: {node.field_32}
    | field_33: {node.field_33}
    | field_34: {node.field_34}
    | field_35: {node.field_35}
    | field_36: {node.field_36}
    | field_37: {node.field_37}
    | field_38: {node.field_38}
    | field_39: {node.field_39}
    | field_40: {node.field_40}
    | field_41: {node.field_41}
    | field_42: {node.field_42}
    | field_43: {node.field_43}
    | field_44: {node.field_44}
    | field_45: {node.field_45}
    | field_46: {node.field_46}
    | field_47: {node.field_47}
    """

    assert render_card(node) == expected
