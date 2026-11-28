"""Near-miss: patches told what to put in place, as home-assistant's
`shelly/test_config_flow.py:5039` patches `PROVISIONING_TIMEOUT` with `0.01`. A patch
given `new` makes no mock, and `patch.dict` puts values, not a mock. Analysed, never
run."""

import os
from unittest import mock

import pytest
from shop import Provisioner, provision

pytestmark = pytest.mark.unit


@mock.patch("shop.PROVISIONING_TIMEOUT", 0.01)
@mock.patch("shop.RETRIES", new=1)
@mock.patch.dict(os.environ, {"TZ": "UTC"})
def test_provision_times_out():
    with (
        mock.patch("shop.BACKOFF", 0),
        mock.patch.object(Provisioner, "region", "eu"),
        mock.patch.object(Provisioner, "port", new=8080),
        mock.patch("shop.HOST", "localhost"),
        mock.patch("shop.SCHEME", new="https"),
        mock.patch.object(Provisioner, "verbose", False),
        mock.patch("shop.CERT", None),
        mock.patch.dict("shop.LIMITS", {"per_minute": 60}),
        mock.patch("shop.connect", autospec=True, side_effect=TimeoutError) as connect,
    ):
        assert provision() == "timed out"
    assert connect.call_count == 1
