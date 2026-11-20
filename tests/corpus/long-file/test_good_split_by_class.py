"""Near-miss: what a split leaves behind, one area per file with its classes, well
under the threshold. Analysed, never run."""

import pytest
from thermostat import Schedule, Thermostat


@pytest.fixture
def thermostat():
    return Thermostat(target=20.0, hysteresis=0.5)


class TestHeating:
    @pytest.mark.parametrize(
        ("current", "decision"), [(19.4, "heat"), (19.8, "idle"), (20.6, "cool")]
    )
    def test_decides_by_the_band(self, thermostat, current, decision):
        assert thermostat.decide(current=current) == decision


class TestSchedule:
    def test_weekday_morning_target(self):
        schedule = Schedule.parse("Mon-Fri 06:30 21.0")

        assert schedule.target_at("Tue", "07:00") == 21.0

    def test_overlapping_entries_are_refused(self):
        with pytest.raises(ValueError, match="overlap"):
            Schedule.parse("Mon 06:00 20.0\nMon 06:00 19.0")
