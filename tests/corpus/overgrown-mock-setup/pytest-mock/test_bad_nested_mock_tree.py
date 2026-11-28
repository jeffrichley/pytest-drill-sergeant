"""Scripting a tree of child mocks, through an alias and `attach_mock`; the plain
values set on its attributes and items are data. Analysed, never run."""

import pytest
from shop import Client, sync

pytestmark = pytest.mark.unit


def test_sync_counts_pages(mocker):  # expect: DS303
    client = mocker.create_autospec(Client, instance=True)
    pages = client.pages
    pages.list.return_value = ["a", "b"]
    pages.get.side_effect = lambda name: {"name": name}
    pages.count.return_value = 2
    client.auth.token = "t"
    client.auth.refresh.return_value = "t2"
    client.limits["per_minute"] = 60
    client.session.headers = {}
    client.session.close.return_value = None
    client.reset_mock(return_value=False)
    client.attach_mock(pages, "book")
    assert sync(client) == {"synced": 2}
