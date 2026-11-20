"""Near-misses: literals the test wrote that pass through the code under test
before the assertion. Analysed, never run."""

from shop import load_config, normalise, price


def test_config_filled_in_place():
    config = {}
    load_config("cfg.toml", into=config)
    assert config == {"debug": True}


def test_lines_appended_by_the_code():
    lines = [1000]
    normalise(lines)
    assert lines == [1000]


def test_expected_literal_against_a_call():
    expected = {"debug": True}
    assert load_config("cfg.toml") == expected


def test_alias_passed_to_code():
    expected = {"debug": True}
    config = expected
    load_config("cfg.toml", into=config)
    assert config == expected


def test_rebound_name():
    total = 0
    total = price(846)
    assert total == 1


def test_multiplied_by_a_non_zero():
    assert price(846) * 2 == 1692
