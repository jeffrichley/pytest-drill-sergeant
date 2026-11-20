"""Skip and xfail marks that say nothing about why. Analysed, never run."""

import sys

import pytest
from billing import Invoice


@pytest.mark.skipif(sys.platform == "win32")  # expect: DS401
def test_invoice_path_uses_forward_slashes():
    assert Invoice(7).path() == "invoices/7.pdf"


@pytest.mark.xfail  # expect: DS401
def test_invoice_total_rounds_half_up():
    assert Invoice(7, amount=2.5).rounded() == 3


@pytest.mark.xfail(strict=True)  # expect: DS401
def test_invoice_rejects_negative_amounts():
    with pytest.raises(ValueError, match="negative"):
        Invoice(7, amount=-1)


@pytest.mark.skipif(sys.version_info < (3, 12), reason="")  # expect: DS401
def test_invoice_number_is_padded():
    assert Invoice(7).number() == "0007"
