"""An async test in a class whose request payload is written out inline, pushing it
past 50 lines. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


class TestImportApi:
    async def test_import_accepts_a_full_batch(self, client):  # expect: DS105
        payload = {
            "batch_id": "b-2026-11-19",
            "source": "warehouse-east",
            "items": [
                {"sku": "A-100", "qty": 4, "bin": "E1-01", "lot": "L-77"},
                {"sku": "A-101", "qty": 1, "bin": "E1-02", "lot": "L-77"},
                {"sku": "A-102", "qty": 9, "bin": "E1-03", "lot": "L-78"},
                {"sku": "B-200", "qty": 2, "bin": "E2-01", "lot": "L-80"},
                {"sku": "B-201", "qty": 7, "bin": "E2-02", "lot": "L-80"},
                {"sku": "B-202", "qty": 3, "bin": "E2-03", "lot": "L-81"},
                {"sku": "C-300", "qty": 5, "bin": "E3-01", "lot": "L-90"},
                {"sku": "C-301", "qty": 8, "bin": "E3-02", "lot": "L-90"},
                {"sku": "C-302", "qty": 6, "bin": "E3-03", "lot": "L-91"},
                {"sku": "D-400", "qty": 1, "bin": "E4-01", "lot": "L-95"},
                {"sku": "D-401", "qty": 2, "bin": "E4-02", "lot": "L-95"},
                {"sku": "D-402", "qty": 4, "bin": "E4-03", "lot": "L-96"},
            ],
            "carrier": {
                "name": "Northline",
                "tracking": "NL-0042-7781",
                "eta": "2026-11-21",
            },
            "contact": {
                "name": "Grace Hopper",
                "phone": "+1-555-0100",
                "email": "grace@example.com",
            },
            "notes": [
                "pallets shrink-wrapped",
                "two cartons damaged on arrival",
                "re-count bin E3-02",
            ],
            "options": {
                "allow_partial": False,
                "notify": True,
                "priority": "normal",
            },
        }

        response = await client.post("/imports", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["batch_id"] == "b-2026-11-19"
        assert body["accepted"] == 12
        assert body["rejected"] == 0
        assert body["total_qty"] == 52
        assert body["carrier"] == "Northline"
        assert body["notes"] == 3
        assert body["source"] == "warehouse-east"
