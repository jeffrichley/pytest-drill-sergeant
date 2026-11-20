"""Mock classes made with no spec, through every import spelling. Analysed, never
run."""

import unittest.mock
from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import NonCallableMagicMock as Thing

import pytest
from shop import fetch, notify, render

pytestmark = pytest.mark.unit


def test_notify_counts_deliveries():
    sender = mock.Mock()  # expect: DS302
    assert notify(sender, "hi").delivered == 1


def test_render_with_magic():
    page = MagicMock(return_value="<p>")  # expect: DS302
    template = Thing()  # expect: DS302
    assert render(page, template) == "<html><p></html>"


async def test_fetch_retries():
    client = AsyncMock(side_effect=[TimeoutError, "ok"])  # expect: DS302
    assert await fetch(client) == "ok"


def test_wrapped_without_spec(real_sender):
    sender = unittest.mock.Mock(wraps=real_sender)  # expect: DS302
    assert notify(sender, "hi").delivered == 1
