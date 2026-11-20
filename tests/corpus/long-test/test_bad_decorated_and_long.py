"""A parametrized test with 52 lines of code: reported on its `def` line, not on its
decorator. Its comments and blank lines don't count, but it is long without them.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("currency", ["GBP", "EUR", "USD"])
def test_invoice_rendering(currency, invoices, renderer):  # expect: DS105
    # Arrange: an invoice with every kind of line the renderer supports.
    invoice = invoices.new(currency=currency, number="INV-0099")
    invoice.add_line(kind="goods", description="Widget", quantity=4, unit=250)
    invoice.add_line(kind="goods", description="Gadget", quantity=1, unit=1200)
    invoice.add_line(kind="goods", description="Sprocket", quantity=10, unit=35)
    invoice.add_line(kind="goods", description="Flange", quantity=2, unit=80)
    invoice.add_line(kind="goods", description="Bracket", quantity=6, unit=15)
    invoice.add_line(kind="service", description="Install", hours=3, rate=80)
    invoice.add_line(kind="service", description="Training", hours=2, rate=95)
    invoice.add_line(kind="service", description="Survey", hours=1, rate=120)
    invoice.add_discount(description="Loyalty", percent=5)
    invoice.add_fee(description="Delivery", amount=150)
    invoice.add_fee(description="Insurance", amount=40)
    invoice.set_terms(days=30)
    invoice.set_due_date("2026-12-20")
    invoice.set_purchase_order("PO-5521")
    invoice.add_note("Thank you for your business.")
    invoice.add_note("Late payments accrue interest.")
    invoice.add_note("Goods remain ours until paid in full.")
    invoice.set_billing_contact("accounts@example.com")
    invoice.set_shipping_contact("dock@example.com")
    invoice.set_reference("Q4 restock")
    invoice.attach("terms.pdf")
    invoice.attach("delivery-note.pdf")
    invoice.set_tax_rate(20)
    invoice.finalise()

    # Act: render to every format.
    html = renderer.to_html(invoice)
    pdf = renderer.to_pdf(invoice)
    csv_rows = renderer.to_rows(invoice)
    text = renderer.to_text(invoice)

    # Assert: the totals.
    assert invoice.goods_total == 2850
    assert invoice.services_total == 550
    assert invoice.discount_total == 170
    assert invoice.fees_total == 190
    assert invoice.grand_total == 3420
    assert invoice.line_count == 8
    assert invoice.due_date == "2026-12-20"
    assert invoice.purchase_order == "PO-5521"

    # Assert: the HTML.
    assert html.count("<tr class='line'>") == 8
    assert "INV-0099" in html
    assert "PO-5521" in html
    assert currency in html

    # Assert: the PDF.
    assert pdf.page_count == 1
    assert pdf.metadata["number"] == "INV-0099"
    assert pdf.metadata["currency"] == currency

    # Assert: the rows.
    assert len(csv_rows) == 11
    assert csv_rows[0] == ["description", "quantity", "unit", "amount"]
    assert csv_rows[-1] == ["total", "", "", "3420"]

    # Assert: the text.
    assert text.startswith("Invoice INV-0099")
    assert "Late payments accrue interest." in text
    assert invoice.notes[0] == "Thank you for your business."
    assert invoice.notes[1] == "Late payments accrue interest."
