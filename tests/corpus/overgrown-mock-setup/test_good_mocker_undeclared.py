"""Near-misses: a `mocker` parameter in a project that declares no pytest-mock, so
its calls are not known to set up mocks. Analysed, never run."""

import pytest
from shop import Client, mirror

pytestmark = pytest.mark.unit


def test_mirror_counts_pages(mocker):
    client = mocker.create_autospec(Client, instance=True)
    mocker.patch("shop.connect", return_value=client)
    mocker.patch("shop.retry_delay", return_value=0)
    client.pages.list.return_value = ["x", "y", "z"]
    client.pages.count.return_value = 3
    client.auth.token = "k"
    client.auth.refresh.return_value = "k2"
    client.limits["per_hour"] = 600
    client.session.headers = {"a": "b"}
    client.session.close.return_value = None
    client.reset_mock(return_value=True)
    assert mirror(client) == {"mirrored": 3}
