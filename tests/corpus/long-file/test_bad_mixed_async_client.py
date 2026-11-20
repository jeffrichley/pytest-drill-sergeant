# expect: DS106
"""Tests for the async weather client: two test classes, then module-level tests an
agent appended below them, some calling the client module, some only fixtures. Past
500 lines. Analysed, never run."""

import json

import pytest
import weather
from weather.units import Celsius, Fahrenheit

pytestmark = pytest.mark.unit

LONDON = (51.5072, -0.1276)
OSLO = (59.9139, 10.7522)


@pytest.fixture
def transport():
    return weather.testing.RecordingTransport()


@pytest.fixture
def client(transport):
    return weather.Client(api_key="test-key", transport=transport)


@pytest.fixture
def forecast_payload():
    return {
        "location": {"lat": 51.5072, "lon": -0.1276, "name": "London"},
        "daily": [
            {"date": "2026-11-19", "min_c": 4.0, "max_c": 9.5, "rain_mm": 1.2},
            {"date": "2026-11-20", "min_c": 3.1, "max_c": 8.0, "rain_mm": 0.0},
            {"date": "2026-11-21", "min_c": 1.8, "max_c": 7.2, "rain_mm": 4.6},
        ],
    }


class TestCurrentConditions:
    """Fetching the weather right now."""

    async def test_requests_the_current_endpoint(self, client, transport):
        """The client asks the `current` endpoint for the given coordinates."""
        transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

        await client.current(*LONDON)

        assert transport.requests[-1].path == "/v2/current"

    async def test_sends_coordinates_as_query_parameters(self, client, transport):
        """Latitude and longitude travel as `lat` and `lon`."""
        transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

        await client.current(*OSLO)

        assert transport.requests[-1].params == {"lat": "59.9139", "lon": "10.7522"}

    async def test_sends_the_api_key_as_a_header(self, client, transport):
        """The key goes in a header, never in the URL where it would be logged."""
        transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

        await client.current(*LONDON)

        assert transport.requests[-1].headers["X-Api-Key"] == "test-key"

    async def test_parses_the_temperature(self, client, transport):
        """The response's `temp_c` becomes a Celsius value."""
        transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

        conditions = await client.current(*LONDON)

        assert conditions.temperature == Celsius(7.5)

    async def test_parses_the_summary(self, client, transport):
        """The summary text is passed through unchanged."""
        transport.respond_with({"temp_c": -2.0, "summary": "Light snow"})

        conditions = await client.current(*OSLO)

        assert conditions.summary == "Light snow"

    async def test_converts_to_fahrenheit_on_request(self, client, transport):
        """Callers who want Fahrenheit get it converted."""
        transport.respond_with({"temp_c": 10.0, "summary": "Sunny"})

        conditions = await client.current(*LONDON, units="imperial")

        assert conditions.temperature == Fahrenheit(50.0)

    async def test_rejects_a_latitude_out_of_range(self, client):  # expect: DS502
        """Latitudes run from -90 to 90; anything else is the caller's bug."""
        with pytest.raises(ValueError, match="latitude"):
            await client.current(91.0, 0.0)

    async def test_rejects_a_longitude_out_of_range(self, client):
        """Longitudes run from -180 to 180."""
        with pytest.raises(ValueError, match="longitude"):
            await client.current(0.0, 181.0)

    async def test_server_error_raises_a_service_error(self, client, transport):
        """A 5xx from the service surfaces as the client's own error type."""
        transport.respond_with_status(503)

        with pytest.raises(weather.ServiceError, match="503"):
            await client.current(*LONDON)

    async def test_bad_key_raises_an_auth_error(self, client, transport):
        """A 401 means the key is wrong, and says so."""
        transport.respond_with_status(401)

        with pytest.raises(weather.AuthError, match="api key"):
            await client.current(*LONDON)


class TestForecast:
    """Fetching the daily forecast."""

    async def test_requests_the_number_of_days_asked_for(self, client, transport):
        """`days` is sent through to the service."""
        transport.respond_with({"location": {}, "daily": []})

        await client.forecast(*LONDON, days=5)

        assert transport.requests[-1].params["days"] == "5"

    async def test_defaults_to_three_days(self, client, transport):
        """Without `days`, the client asks for three."""
        transport.respond_with({"location": {}, "daily": []})

        await client.forecast(*LONDON)

        assert transport.requests[-1].params["days"] == "3"

    async def test_parses_each_day(self, client, transport, forecast_payload):
        """Every entry in `daily` becomes one forecast day."""
        transport.respond_with(forecast_payload)

        forecast = await client.forecast(*LONDON)

        assert [day.date.isoformat() for day in forecast.days] == [
            "2026-11-19",
            "2026-11-20",
            "2026-11-21",
        ]

    async def test_parses_daily_extremes(self, client, transport, forecast_payload):
        """Minimum and maximum temperatures come through per day."""
        transport.respond_with(forecast_payload)

        forecast = await client.forecast(*LONDON)

        assert (forecast.days[0].low, forecast.days[0].high) == (
            Celsius(4.0),
            Celsius(9.5),
        )

    async def test_wettest_day(self, client, transport, forecast_payload):
        """The forecast knows which of its days has the most rain."""
        transport.respond_with(forecast_payload)

        forecast = await client.forecast(*LONDON)

        assert forecast.wettest_day().date.isoformat() == "2026-11-21"

    async def test_dry_days(self, client, transport, forecast_payload):
        """Days with no rain at all are listed as dry."""
        transport.respond_with(forecast_payload)

        forecast = await client.forecast(*LONDON)

        assert [day.date.isoformat() for day in forecast.dry_days()] == ["2026-11-20"]

    async def test_location_name_is_kept(self, client, transport, forecast_payload):
        """The service's place name is kept for display."""
        transport.respond_with(forecast_payload)

        forecast = await client.forecast(*LONDON)

        assert forecast.location_name == "London"

    async def test_more_than_fourteen_days_is_refused(self, client):  # expect: DS502
        """The service forecasts at most two weeks ahead."""
        with pytest.raises(ValueError, match="14 days"):
            await client.forecast(*LONDON, days=15)

    async def test_zero_days_is_refused(self, client):
        """A forecast for no days is a mistake."""
        with pytest.raises(ValueError, match="at least one day"):
            await client.forecast(*LONDON, days=0)

    async def test_missing_daily_field_is_a_service_error(self, client, transport):
        """A payload without `daily` is malformed, and the error says so."""
        transport.respond_with({"location": {"name": "London"}})

        with pytest.raises(weather.ServiceError, match="daily"):
            await client.forecast(*LONDON)

    async def test_forecast_is_cached_for_ten_minutes(self, client, transport):
        """A second call within the cache window makes no new request."""
        transport.respond_with({"location": {}, "daily": []})
        await client.forecast(*LONDON)

        await client.forecast(*LONDON)

        assert len(transport.requests) == 1

    async def test_different_coordinates_are_cached_apart(self, client, transport):
        """The cache is keyed on the location, not shared between them."""
        transport.respond_with({"location": {}, "daily": []})
        await client.forecast(*LONDON)

        await client.forecast(*OSLO)

        assert len(transport.requests) == 2


async def test_alerts_endpoint_is_requested(client, transport):
    transport.respond_with({"alerts": []})

    await client.alerts(*LONDON)

    assert transport.requests[-1].path == "/v2/alerts"


async def test_no_alerts_gives_an_empty_list(client, transport):
    transport.respond_with({"alerts": []})

    assert await client.alerts(*LONDON) == []


async def test_alerts_are_parsed_with_their_severity(client, transport):
    transport.respond_with(
        {
            "alerts": [
                {"title": "Wind", "severity": "amber", "until": "2026-11-20T18:00"},
                {"title": "Rain", "severity": "yellow", "until": "2026-11-21T09:00"},
            ]
        }
    )

    alerts = await client.alerts(*LONDON)

    assert [(a.title, a.severity) for a in alerts] == [
        ("Wind", "amber"),
        ("Rain", "yellow"),
    ]


async def test_alerts_sorted_most_severe_first(client, transport):
    transport.respond_with(
        {
            "alerts": [
                {"title": "Rain", "severity": "yellow", "until": "2026-11-21T09:00"},
                {"title": "Flood", "severity": "red", "until": "2026-11-22T12:00"},
            ]
        }
    )

    alerts = await client.alerts(*LONDON)

    assert [a.title for a in alerts] == ["Flood", "Rain"]


async def test_unknown_severity_is_a_service_error(client, transport):
    transport.respond_with(
        {"alerts": [{"title": "Fog", "severity": "purple", "until": "2026-11-20"}]}
    )

    with pytest.raises(weather.ServiceError, match="severity"):
        await client.alerts(*LONDON)


async def test_rate_limit_waits_for_the_retry_after_header(client, transport):
    transport.respond_with_status(429, headers={"Retry-After": "0"})
    transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

    conditions = await client.current(*LONDON)

    assert conditions.summary == "Cloudy"


async def test_rate_limit_gives_up_after_three_tries(client, transport):
    for _ in range(3):
        transport.respond_with_status(429, headers={"Retry-After": "0"})

    with pytest.raises(weather.RateLimited, match="3 attempts"):
        await client.current(*LONDON)


async def test_timeout_raises_a_service_error(client, transport):
    transport.time_out_next()

    with pytest.raises(weather.ServiceError, match="timed out"):
        await client.current(*LONDON)


async def test_client_closes_its_transport(client, transport):
    await client.close()

    assert transport.closed is True


async def test_client_works_as_an_async_context_manager(transport):
    async with weather.Client(api_key="k", transport=transport) as inside:
        transport.respond_with({"temp_c": 1.0, "summary": "Frost"})
        await inside.current(*OSLO)

    assert transport.closed is True


def test_client_requires_an_api_key(transport):
    with pytest.raises(ValueError, match="api_key"):
        weather.Client(api_key="", transport=transport)


def test_client_reads_the_base_url_from_settings(transport):
    settings = weather.Settings(base_url="https://staging.weather.example")

    client = weather.Client(api_key="k", transport=transport, settings=settings)

    assert client.base_url == "https://staging.weather.example"


def test_settings_reject_a_plain_http_url():
    with pytest.raises(ValueError, match="https"):
        weather.Settings(base_url="http://weather.example")


def test_settings_default_timeout_is_ten_seconds():
    assert weather.Settings().timeout == 10.0


def test_settings_load_from_json(tmp_path):
    path = tmp_path / "weather.json"
    path.write_text(json.dumps({"base_url": "https://w.example", "timeout": 3}))

    settings = weather.Settings.from_file(path)

    assert (settings.base_url, settings.timeout) == ("https://w.example", 3.0)


def test_settings_unknown_key_is_refused(tmp_path):
    path = tmp_path / "weather.json"
    path.write_text(json.dumps({"base_url": "https://w.example", "colour": "blue"}))

    with pytest.raises(ValueError, match="colour"):
        weather.Settings.from_file(path)


def test_celsius_to_fahrenheit():
    assert Celsius(100).to_fahrenheit() == Fahrenheit(212)


def test_fahrenheit_to_celsius():
    assert Fahrenheit(32).to_celsius() == Celsius(0)


def test_celsius_below_absolute_zero_is_refused():
    with pytest.raises(ValueError, match="absolute zero"):
        Celsius(-274)


def test_celsius_values_compare():
    assert sorted([Celsius(5), Celsius(-3), Celsius(0)]) == [
        Celsius(-3),
        Celsius(0),
        Celsius(5),
    ]


def test_celsius_formats_with_one_decimal():
    assert format(Celsius(7.25), "") == "7.2°C"


def test_fahrenheit_formats_with_no_decimals():
    assert format(Fahrenheit(44.6), "") == "45°F"


def test_recorded_requests_start_empty(transport):
    assert transport.requests == []


def test_recording_transport_replays_in_order(transport):
    transport.respond_with({"n": 1})
    transport.respond_with({"n": 2})

    assert [transport.next_response()["n"] for _ in range(2)] == [1, 2]


def test_recording_transport_with_nothing_queued_raises(transport):
    with pytest.raises(LookupError, match="no response queued"):
        transport.next_response()


def test_forecast_payload_fixture_has_three_days(forecast_payload):
    assert [day["date"] for day in forecast_payload["daily"]] == [
        "2026-11-19",
        "2026-11-20",
        "2026-11-21",
    ]


async def test_hourly_endpoint_is_requested(client, transport):
    transport.respond_with({"hourly": []})

    await client.hourly(*LONDON, hours=6)

    assert transport.requests[-1].params["hours"] == "6"


async def test_hourly_parses_each_hour(client, transport):
    transport.respond_with(
        {
            "hourly": [
                {"time": "2026-11-19T09:00", "temp_c": 5.0},
                {"time": "2026-11-19T10:00", "temp_c": 5.5},
                {"time": "2026-11-19T11:00", "temp_c": 6.2},
            ]
        }
    )

    hours = await client.hourly(*LONDON, hours=3)

    assert [h.temperature for h in hours] == [Celsius(5.0), Celsius(5.5), Celsius(6.2)]


async def test_hourly_more_than_48_hours_is_refused(client):
    with pytest.raises(ValueError, match="48 hours"):
        await client.hourly(*LONDON, hours=49)


async def test_air_quality_index_is_parsed(client, transport):
    transport.respond_with({"aqi": 42, "band": "good"})

    quality = await client.air_quality(*LONDON)

    assert (quality.index, quality.band) == (42, "good")


async def test_air_quality_band_is_derived_when_missing(client, transport):
    transport.respond_with({"aqi": 160})

    quality = await client.air_quality(*LONDON)

    assert quality.band == "unhealthy"


async def test_sunrise_and_sunset_are_parsed(client, transport):
    transport.respond_with({"sunrise": "07:21", "sunset": "16:05"})

    sun = await client.sun(*LONDON, date="2026-11-19")

    assert (sun.sunrise.isoformat(), sun.sunset.isoformat()) == ("07:21:00", "16:05:00")


async def test_daylight_length(client, transport):
    transport.respond_with({"sunrise": "07:21", "sunset": "16:05"})

    sun = await client.sun(*LONDON, date="2026-11-19")

    assert sun.daylight_minutes == 524


async def test_polar_night_has_no_sunrise(client, transport):
    transport.respond_with({"sunrise": None, "sunset": None})

    sun = await client.sun(69.6492, 18.9553, date="2026-12-21")

    assert sun.daylight_minutes == 0


async def test_user_agent_names_the_client_version(client, transport):  # expect: DS502
    transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

    await client.current(*LONDON)

    assert transport.requests[-1].headers["User-Agent"] == "weather-client/2.4"


async def test_requests_ask_for_gzip(client, transport):
    transport.respond_with({"temp_c": 7.5, "summary": "Cloudy"})

    await client.current(*LONDON)

    assert transport.requests[-1].headers["Accept-Encoding"] == "gzip"


async def test_gzip_responses_are_decoded(client, transport):
    transport.respond_with_gzip({"temp_c": 3.0, "summary": "Mist"})

    conditions = await client.current(*LONDON)

    assert conditions.summary == "Mist"


async def test_station_lookup_returns_the_nearest_station(client, transport):
    transport.respond_with({"stations": [{"id": "EGLC", "km": 11.2}]})

    station = await client.nearest_station(*LONDON)

    assert (station.id, station.distance_km) == ("EGLC", 11.2)


async def test_station_lookup_with_none_nearby_returns_none(client, transport):
    transport.respond_with({"stations": []})

    assert await client.nearest_station(0.0, -160.0) is None
