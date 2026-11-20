import pytest

from pytest_drill_sergeant.checks import CHECKS

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("check", CHECKS, ids=lambda c: c.code)
def test_agent_guide_teaches_each_check_from_the_registry(cli, check):
    result = cli("agent-guide")

    assert result.exit_code == 0, result.output
    assert check.why in result.output
    assert check.good_example in result.output


def test_agent_guide_states_the_waiver_rule(cli):
    output = cli("agent-guide").output

    assert "explicit yes" in output
