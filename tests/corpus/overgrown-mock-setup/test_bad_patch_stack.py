"""Stacks of patches, as decorators and as `with` items, each counting as setup.
Analysed, never run."""

import os
from unittest import mock
from unittest.mock import patch

from shop import Mailer, report


@patch("shop.load_orders", autospec=True)
@patch("shop.load_refunds", autospec=True)
@patch("shop.load_rates", autospec=True)
@patch("shop.today", autospec=True)
@patch.object(Mailer, "deliver", autospec=True)
@patch.dict(os.environ, {"TZ": "UTC"})
def test_daily_report(deliver, today, rates, refunds, orders):  # expect: DS303
    orders.return_value = [100, 200]
    refunds.return_value = [50]
    rates.return_value = {"EUR": 1.0}
    today.return_value = "2026-01-01"
    deliver.return_value = True
    assert report() == "2026-01-01: 250 EUR"


class TestReport:
    def test_weekly_report(self, mocker):  # expect: DS303
        with (
            mock.patch("shop.load_orders", autospec=True) as orders,
            mock.patch("shop.load_refunds", autospec=True) as refunds,
            mock.patch("shop.load_rates", autospec=True) as rates,
            mock.patch("shop.today", autospec=True) as today,
        ):
            orders.return_value = [100, 200]
            refunds.return_value = [50]
            rates.return_value = {"EUR": 1.0}
            today.return_value = "2026-01-01"
            deliver = mocker.patch.object(Mailer, "deliver", autospec=True)
            deliver.return_value = True
            deliver.side_effect = None
            assert report(weekly=True) == "week of 2026-01-01: 250 EUR"
