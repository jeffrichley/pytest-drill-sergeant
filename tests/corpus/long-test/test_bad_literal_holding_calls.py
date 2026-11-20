"""An async test in a class whose request payload builds each item with a call: a
literal holding a call is code, not data, so it still counts line by line, and the
test has 53 lines of code. Analysed, never run."""

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
