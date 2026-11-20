"""A parametrized test whose body is long: reported on its `def` line, not on its
decorator, and its comments and blank lines count. Analysed, never run."""

import pytest


@pytest.mark.parametrize("currency", ["GBP", "EUR", "USD"])
def test_invoice_rendering(currency, invoices, renderer):  # expect: DS105
    # Build an invoice with every kind of line the renderer supports.
    invoice = invoices.new(currency=currency, number="INV-0099")

    # Goods lines.
    invoice.add_line(kind="goods", description="Widget", quantity=4, unit=250)
    invoice.add_line(kind="goods", description="Gadget", quantity=1, unit=1200)
    invoice.add_line(kind="goods", description="Sprocket", quantity=10, unit=35)

    # Service lines.
    invoice.add_line(kind="service", description="Install", hours=3, rate=80)
    invoice.add_line(kind="service", description="Training", hours=2, rate=95)

    # A discount and a fee.
    invoice.add_discount(description="Loyalty", percent=5)
    invoice.add_fee(description="Delivery", amount=150)

    # Payment terms and notes.
    invoice.set_terms(days=30)
    invoice.add_note("Thank you for your business.")
    invoice.add_note("Late payments accrue interest.")

    # Render to every format.
    html = renderer.to_html(invoice)
    pdf = renderer.to_pdf(invoice)
    csv_rows = renderer.to_rows(invoice)

    # The totals.
    assert invoice.goods_total == 2550
    assert invoice.services_total == 430
    assert invoice.discount_total == 149
    assert invoice.fees_total == 150
    assert invoice.grand_total == 2981

    # The HTML.
    assert html.count("<tr class='line'>") == 5
    assert "INV-0099" in html

    # The PDF.
    assert pdf.page_count == 1
    assert pdf.metadata["number"] == "INV-0099"

    # The rows.
    assert len(csv_rows) == 8
    assert csv_rows[0] == ["description", "quantity", "unit", "amount"]
    assert csv_rows[-1] == ["total", "", "", "2981"]

    # The notes.
    assert invoice.notes == [
        "Thank you for your business.",
        "Late payments accrue interest.",
    ]
