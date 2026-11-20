"""Near-misses: skips and xfails that say why, by keyword, by position or from a name.

Analysed, never run.
"""

import os
import sys

import pytest
from billing import Invoice

WINDOWS_PATHS = "Windows paths use backslashes, see #88"


@pytest.mark.skipif(sys.platform == "win32", reason=WINDOWS_PATHS)
def test_invoice_path_uses_forward_slashes():
    assert Invoice(7).path() == "invoices/7.pdf"


@pytest.mark.xfail(reason="rounding is banker's until #91 lands", strict=True)
def test_invoice_total_rounds_half_up():
    assert Invoice(7, amount=2.5).rounded() == 3


def test_invoice_mails_a_copy():
    if "SMTP_HOST" not in os.environ:
        pytest.skip("needs an SMTP server")
    assert Invoice(7).mail(os.environ["SMTP_HOST"]) == "250 OK"


def test_invoice_signs_the_pdf():
    if not Invoice.can_sign():
        pytest.skip(reason="no signing key in this environment")
    assert Invoice(7).signed() == "signed"


def test_invoice_renders_in_french():
    invoice = Invoice(7, locale="fr")
    if not invoice.has_translations():
        pytest.xfail(reason=WINDOWS_PATHS)
    assert invoice.title() == "Facture"
