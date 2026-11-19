"""Near-misses: injected clocks, fixed datetimes and `datetime` calls that don't read
the clock. Analysed, never run.
"""

from datetime import date, datetime

from billing import FakeClock, Invoice


def now():
    return datetime(2026, 1, 1)


def test_invoice_dated_by_an_injected_clock(clock):
    invoice = Invoice.issue(clock=clock)
    assert invoice.issued == clock.now()


def test_invoice_dated_by_a_fake_clock():
    clock = FakeClock(datetime(2026, 1, 1))
    assert Invoice.issue(clock=clock).date == clock.today()


def test_invoice_parses_a_fixed_date():
    invoice = Invoice.parse("2026-01-01")
    assert invoice.date == date.fromisoformat("2026-01-01")
    assert invoice.issued == datetime(2026, 1, 1)


def test_local_function_named_now():
    assert Invoice.issue(at=now()).issued == datetime(2026, 1, 1)


def test_clock_passed_but_not_read():
    invoice = Invoice.issue(clock=datetime.now)
    assert invoice.clock is datetime.now


def test_converts_a_fixed_timestamp():
    import time

    assert Invoice.from_timestamp(0).year == time.gmtime(0).tm_year
