# expect: DS106
"""Tests for the duration parser and formatter: no classes, just module-level
tests and their tables, grown one case at a time past 500 lines. Analysed, never
run."""

import pytest
from durations import Duration, format_duration, parse_duration

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("1s", 1),
        ("2s", 2),
        ("3s", 3),
        ("5s", 5),
        ("7s", 7),
        ("10s", 10),
        ("12s", 12),
        ("15s", 15),
        ("30s", 30),
        ("45s", 45),
        ("90s", 90),
        ("120s", 120),
        ("1m", 60),
        ("2m", 120),
        ("3m", 180),
        ("5m", 300),
        ("7m", 420),
        ("10m", 600),
        ("12m", 720),
        ("15m", 900),
        ("30m", 1800),
        ("45m", 2700),
        ("90m", 5400),
        ("120m", 7200),
        ("1h", 3600),
        ("2h", 7200),
        ("3h", 10800),
        ("5h", 18000),
        ("7h", 25200),
        ("10h", 36000),
        ("12h", 43200),
        ("15h", 54000),
        ("30h", 108000),
        ("45h", 162000),
        ("90h", 324000),
        ("120h", 432000),
        ("1d", 86400),
        ("2d", 172800),
        ("3d", 259200),
        ("5d", 432000),
        ("7d", 604800),
        ("10d", 864000),
        ("12d", 1036800),
        ("15d", 1296000),
        ("30d", 2592000),
        ("45d", 3888000),
        ("90d", 7776000),
        ("120d", 10368000),
        ("1w", 604800),
        ("2w", 1209600),
        ("3w", 1814400),
        ("5w", 3024000),
        ("7w", 4233600),
        ("10w", 6048000),
        ("12w", 7257600),
        ("15w", 9072000),
        ("30w", 18144000),
        ("45w", 27216000),
        ("90w", 54432000),
        ("120w", 72576000),
    ],
)
def test_parses_a_single_unit(text, seconds):
    assert parse_duration(text).seconds == seconds


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("1h0m0s", 3600),
        ("1h0m1s", 3601),
        ("1h0m30s", 3630),
        ("1h0m45s", 3645),
        ("1h5m0s", 3900),
        ("1h5m1s", 3901),
        ("1h5m30s", 3930),
        ("1h5m45s", 3945),
        ("1h15m0s", 4500),
        ("1h15m1s", 4501),
        ("1h15m30s", 4530),
        ("1h15m45s", 4545),
        ("1h30m0s", 5400),
        ("1h30m1s", 5401),
        ("1h30m30s", 5430),
        ("1h30m45s", 5445),
        ("1h45m0s", 6300),
        ("1h45m1s", 6301),
        ("1h45m30s", 6330),
        ("1h45m45s", 6345),
        ("1h59m0s", 7140),
        ("1h59m1s", 7141),
        ("1h59m30s", 7170),
        ("1h59m45s", 7185),
        ("2h0m0s", 7200),
        ("2h0m1s", 7201),
        ("2h0m30s", 7230),
        ("2h0m45s", 7245),
        ("2h5m0s", 7500),
        ("2h5m1s", 7501),
        ("2h5m30s", 7530),
        ("2h5m45s", 7545),
        ("2h15m0s", 8100),
        ("2h15m1s", 8101),
        ("2h15m30s", 8130),
        ("2h15m45s", 8145),
        ("2h30m0s", 9000),
        ("2h30m1s", 9001),
        ("2h30m30s", 9030),
        ("2h30m45s", 9045),
        ("2h45m0s", 9900),
        ("2h45m1s", 9901),
        ("2h45m30s", 9930),
        ("2h45m45s", 9945),
        ("2h59m0s", 10740),
        ("2h59m1s", 10741),
        ("2h59m30s", 10770),
        ("2h59m45s", 10785),
        ("3h0m0s", 10800),
        ("3h0m1s", 10801),
        ("3h0m30s", 10830),
        ("3h0m45s", 10845),
        ("3h5m0s", 11100),
        ("3h5m1s", 11101),
        ("3h5m30s", 11130),
        ("3h5m45s", 11145),
        ("3h15m0s", 11700),
        ("3h15m1s", 11701),
        ("3h15m30s", 11730),
        ("3h15m45s", 11745),
        ("3h30m0s", 12600),
        ("3h30m1s", 12601),
        ("3h30m30s", 12630),
        ("3h30m45s", 12645),
        ("3h45m0s", 13500),
        ("3h45m1s", 13501),
        ("3h45m30s", 13530),
        ("3h45m45s", 13545),
        ("3h59m0s", 14340),
        ("3h59m1s", 14341),
        ("3h59m30s", 14370),
        ("3h59m45s", 14385),
        ("6h0m0s", 21600),
        ("6h0m1s", 21601),
        ("6h0m30s", 21630),
        ("6h0m45s", 21645),
        ("6h5m0s", 21900),
        ("6h5m1s", 21901),
        ("6h5m30s", 21930),
        ("6h5m45s", 21945),
        ("6h15m0s", 22500),
        ("6h15m1s", 22501),
        ("6h15m30s", 22530),
        ("6h15m45s", 22545),
        ("6h30m0s", 23400),
        ("6h30m1s", 23401),
        ("6h30m30s", 23430),
        ("6h30m45s", 23445),
        ("6h45m0s", 24300),
        ("6h45m1s", 24301),
        ("6h45m30s", 24330),
        ("6h45m45s", 24345),
        ("6h59m0s", 25140),
        ("6h59m1s", 25141),
        ("6h59m30s", 25170),
        ("6h59m45s", 25185),
        ("12h0m0s", 43200),
        ("12h0m1s", 43201),
        ("12h0m30s", 43230),
        ("12h0m45s", 43245),
        ("12h5m0s", 43500),
        ("12h5m1s", 43501),
        ("12h5m30s", 43530),
        ("12h5m45s", 43545),
        ("12h15m0s", 44100),
        ("12h15m1s", 44101),
        ("12h15m30s", 44130),
        ("12h15m45s", 44145),
        ("12h30m0s", 45000),
        ("12h30m1s", 45001),
        ("12h30m30s", 45030),
        ("12h30m45s", 45045),
        ("12h45m0s", 45900),
        ("12h45m1s", 45901),
        ("12h45m30s", 45930),
        ("12h45m45s", 45945),
        ("12h59m0s", 46740),
        ("12h59m1s", 46741),
        ("12h59m30s", 46770),
        ("12h59m45s", 46785),
        ("23h0m0s", 82800),
        ("23h0m1s", 82801),
        ("23h0m30s", 82830),
        ("23h0m45s", 82845),
        ("23h5m0s", 83100),
        ("23h5m1s", 83101),
        ("23h5m30s", 83130),
        ("23h5m45s", 83145),
        ("23h15m0s", 83700),
        ("23h15m1s", 83701),
        ("23h15m30s", 83730),
        ("23h15m45s", 83745),
        ("23h30m0s", 84600),
        ("23h30m1s", 84601),
        ("23h30m30s", 84630),
        ("23h30m45s", 84645),
        ("23h45m0s", 85500),
        ("23h45m1s", 85501),
        ("23h45m30s", 85530),
        ("23h45m45s", 85545),
        ("23h59m0s", 86340),
        ("23h59m1s", 86341),
        ("23h59m30s", 86370),
        ("23h59m45s", 86385),
    ],
)
def test_parses_hours_minutes_and_seconds_together(text, seconds):
    assert parse_duration(text).seconds == seconds


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("1 day 0 hours", 86400),
        ("1 day 4 hours", 100800),
        ("1 day 23 hours", 169200),
        ("3 days 0 hours", 259200),
        ("3 days 4 hours", 273600),
        ("3 days 23 hours", 342000),
        ("7 days 0 hours", 604800),
        ("7 days 4 hours", 619200),
        ("7 days 23 hours", 687600),
    ],
)
def test_parses_spelled_out_units(text, seconds):
    assert parse_duration(text).seconds == seconds


@pytest.mark.parametrize(
    "text",
    [
        "",
        " ",
        "h",
        "1",
        "1x",
        "1hh",
        "h1",
        "-1s",
        "1.5.2h",
        "1h-5m",
        "one hour",
        "1 fortnight",
        "1s1h",
        "1m1m",
        "99999999999999999999d",
        "1 h 2",
        "\t",
        "1_h",
        "1h,",
        ",1h",
        "1H",
        "1 S",
        "1w2",
        "0x10s",
        "1e3s",
        "NaNs",
        "infd",
    ],
)
def test_rejects_malformed_text(text):
    with pytest.raises(ValueError, match="duration"):
        parse_duration(text)


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (0, "0s"),
        (1, "1s"),
        (59, "59s"),
        (60, "1m"),
        (61, "1m1s"),
        (119, "1m59s"),
        (3599, "59m59s"),
        (3600, "1h"),
        (3661, "1h1m1s"),
        (86399, "23h59m59s"),
        (86400, "1d"),
        (90061, "1d1h1m1s"),
        (604800, "1w"),
        (694861, "1w1d1h1m1s"),
    ],
)
def test_formats_seconds_largest_unit_first(seconds, text):
    assert format_duration(seconds) == text


def test_round_trips_through_text():
    assert parse_duration(format_duration(694861)).seconds == 694861


def test_zero_is_allowed():  # expect: DS502
    assert parse_duration("0s").seconds == 0


def test_whitespace_around_the_text_is_ignored():
    assert parse_duration("  90m  ").seconds == 5400


def test_durations_add():
    total = Duration(seconds=90) + Duration(seconds=30)

    assert total.seconds == 120


def test_durations_subtract_to_zero_but_not_below():
    with pytest.raises(ValueError, match="negative"):
        Duration(seconds=30) - Duration(seconds=31)


def test_durations_compare_by_length():
    assert sorted([Duration(seconds=60), Duration(seconds=5)]) == [
        Duration(seconds=5),
        Duration(seconds=60),
    ]


def test_duration_multiplies_by_an_integer():
    assert (Duration(seconds=45) * 4).seconds == 180


def test_duration_divides_into_whole_parts():
    assert Duration(seconds=3600) // 7 == Duration(seconds=514)


def test_minutes_property_rounds_down():
    assert Duration(seconds=119).minutes == 1


def test_hours_property_rounds_down():
    assert Duration(seconds=7199).hours == 1


def test_iso_8601_output():
    assert Duration(seconds=90061).isoformat() == "P1DT1H1M1S"


def test_iso_8601_input():
    assert parse_duration("PT1H30M").seconds == 5400


def test_repr_shows_the_text_form():
    assert repr(Duration(seconds=3661)) == "Duration('1h1m1s')"


def test_bool_is_false_only_for_zero():
    assert [bool(Duration(seconds=0)), bool(Duration(seconds=1))] == [False, True]


def test_hash_matches_for_equal_durations():
    assert len({Duration(seconds=60), parse_duration("1m")}) == 1


def test_humanize_rounds_to_the_largest_unit():  # expect: DS502
    assert Duration(seconds=3700).humanize() == "about an hour"


def test_humanize_says_moments_for_under_ten_seconds():
    assert Duration(seconds=9).humanize() == "a few moments"


def test_humanize_pluralises_days():  # expect: DS502
    assert Duration(seconds=3 * 86400).humanize() == "3 days"


def test_humanize_uses_weeks_from_fourteen_days():
    assert Duration(seconds=14 * 86400).humanize() == "2 weeks"


def test_total_of_an_empty_list_is_zero():
    assert Duration.total([]) == Duration(seconds=0)


def test_total_sums_every_duration():
    assert Duration.total([parse_duration("1h"), parse_duration("30m")]).seconds == 5400


def test_parse_accepts_a_custom_unit_table():
    parsed = parse_duration("2 sprints", units={"sprint": 14 * 86400})

    assert parsed.seconds == 2419200


def test_custom_units_do_not_leak_into_later_parses():
    parse_duration("1 sprint", units={"sprint": 14 * 86400})

    with pytest.raises(ValueError, match="duration"):
        parse_duration("1 sprint")


def test_strict_mode_rejects_spelled_out_units():
    with pytest.raises(ValueError, match="strict"):
        parse_duration("3 days", strict=True)


def test_strict_mode_accepts_compact_units():
    assert parse_duration("3d", strict=True).seconds == 259200


def test_format_with_a_separator():
    assert format_duration(3661, sep=" ") == "1h 1m 1s"


def test_format_with_a_maximum_number_of_parts():
    assert format_duration(694861, max_parts=2) == "1w1d"


def test_format_rejects_negative_seconds():
    with pytest.raises(ValueError, match="negative"):
        format_duration(-1)


def test_format_long_names():
    assert format_duration(7260, long=True) == "2 hours 1 minute"


def test_from_timedelta_keeps_whole_seconds():
    assert Duration.from_seconds_float(90.9).seconds == 90


def test_duration_is_immutable():
    duration = Duration(seconds=5)

    with pytest.raises(AttributeError, match="seconds"):
        duration.seconds = 6


def test_max_picks_the_longest():
    assert max(parse_duration("1h"), parse_duration("59m")) == Duration(seconds=3600)


def test_parse_reads_a_clock_style_duration():
    assert parse_duration("01:30:15").seconds == 5415


def test_clock_style_without_hours_reads_minutes_and_seconds():
    assert parse_duration("12:05").seconds == 725


def test_clock_style_rejects_sixty_minutes():
    with pytest.raises(ValueError, match="minutes"):
        parse_duration("01:60:00")


def test_format_clock_style():  # expect: DS502
    assert format_duration(5415, clock=True) == "01:30:15"


def test_format_clock_style_past_a_day_keeps_counting_hours():
    assert format_duration(90061, clock=True) == "25:01:01"


def test_parse_duration_returns_a_duration():
    assert parse_duration("1s") == Duration(seconds=1)


def test_min_picks_the_shortest():
    assert min(parse_duration("1d"), parse_duration("25h")) == Duration(seconds=86400)


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (0, "no time"),
        (1, "a few moments"),
        (9, "a few moments"),
        (10, "10 seconds"),
        (44, "44 seconds"),
        (45, "about a minute"),
        (89, "about a minute"),
        (90, "2 minutes"),
        (600, "10 minutes"),
        (2640, "44 minutes"),
        (2700, "about an hour"),
        (5399, "about an hour"),
        (5400, "2 hours"),
        (36000, "10 hours"),
        (77400, "about a day"),
        (129599, "about a day"),
        (129600, "2 days"),
        (432000, "5 days"),
        (1209600, "2 weeks"),
        (2419200, "4 weeks"),
    ],
)
def test_humanize_thresholds(seconds, text):
    assert Duration(seconds=seconds).humanize() == text
