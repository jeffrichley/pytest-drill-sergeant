"""Near-misses: clock reads in fixtures and helpers, and a fixture that shadows the
`datetime` import. Analysed, never run.
"""

from datetime import datetime

import pytest
from billing import Invoice

pytestmark = pytest.mark.unit


def stamp():
    return datetime.now()


@pytest.fixture
def issued_invoice():
    return Invoice.issue(at=datetime.now())


def test_invoice_issued(issued_invoice):
    assert issued_invoice.issued.year == 2026


def test_fixture_shadows_the_import(datetime):
    datetime.now.return_value = 0
    assert Invoice.issue(clock=datetime).issued == 0
