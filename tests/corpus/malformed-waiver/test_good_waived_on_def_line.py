"""Complete waivers on a test's `def` line silence that check anywhere in the test."""

import pytest
from app import load, main, start_server
from calc import add


def test_cli_smoke():  # drill: waive DS101 -- the exit code is checked by CI
    main(["--help"])


@pytest.mark.slow
def test_loads_anything():  # drill: waive DS201 -- any loaded value will do
    value = load("config.toml")
    assert value is not None


class TestServer:
    async def test_starts(self):  # drill: waive DS101 -- startup is the behaviour
        await start_server()


def test_unused_waiver():  # drill: waive DS201 -- matches nothing, reported nowhere
    assert add(1, 2) == 3
