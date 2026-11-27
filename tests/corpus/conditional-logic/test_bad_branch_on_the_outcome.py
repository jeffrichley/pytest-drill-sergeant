"""Tests that branch on the outcome and assert differently on each path, so they pass
whichever way the code goes. One came from weak-assertion's near-misses, and still
is one: a strong assertion in a branch counts (DS201). Analysed, never run."""

import pytest
from shop import make_order

pytestmark = pytest.mark.unit


def test_strong_assertion_inside_a_branch_still_counts():
    order = make_order(lines=[1000])
    if order.total:  # expect: DS107
        assert order.total == 1000
    assert order is not None


def test_parse_reply(parser):
    reply = parser.parse(b"OK 3\r\n")
    match reply.kind:  # expect: DS107
        case "ok":
            assert reply.count == 3
        case "error":
            pytest.fail(reply.message)


def test_upgrade_path(db):
    version = db.migrate()

    if version >= 3:  # expect: DS107
        assert db.has_table("events")


def test_retry_until_it_works(client):
    response = client.get("/health")
    if response.status_code != 200:  # expect: DS107
        response = client.get("/health")
        if response.status_code != 200:
            raise AssertionError(response.text)
    assert response.json() == {"status": "up"}


class TestExport:
    def test_export_format(self, exporter, settings):
        data = exporter.export()
        if settings.compress:  # expect: DS107
            with pytest.raises(UnicodeDecodeError, match="utf-8"):
                data.decode()
        elif settings.format == "csv":
            assert data.startswith(b"id,")
