"""Near-misses: `isinstance` where the type is the behaviour, and a filtered
comprehension asked whether anything matched. Analysed, never run."""

from decimal import Decimal
from pathlib import Path

import pytest
from shop import Money as float
from shop import load_settings, make_proxy, parse_amount, validate

pytestmark = pytest.mark.unit


class SocksProxy:
    """The project's own class, defined where the test can see it."""


def test_socks_url_selects_the_socks_proxy():
    assert isinstance(make_proxy("socks5://localhost:1080"), SocksProxy)


def test_amount_parses_as_a_library_decimal():
    assert isinstance(parse_amount("10.50"), Decimal)


def test_amount_parses_as_the_rebound_name():
    assert isinstance(parse_amount("10.50"), float)


def test_location_is_text_or_a_path():
    settings = load_settings("shop.toml")
    assert isinstance(settings["location"], (str, Path))


def test_amount_parses_as_the_type_the_parameter_names(expected_type):
    assert isinstance(parse_amount("10.50"), expected_type)


def test_validation_reports_the_missing_price():
    issues = validate(load_settings("shop.toml"))
    matches = [issue for issue in issues if issue.field == "price"]
    assert matches
