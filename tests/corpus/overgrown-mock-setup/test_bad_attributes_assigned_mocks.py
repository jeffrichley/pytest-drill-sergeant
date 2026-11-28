"""A mock whose attributes are each assigned a mock, as home-assistant's
`shelly/test_config_flow.py:5039` builds its `mock_ip_device`: each attribute
assigned a mock is a target scripted, while its plain data attributes are not.
Analysed, never run."""

from unittest.mock import AsyncMock

import pytest
from shop import Device, provision

pytestmark = pytest.mark.unit


async def test_provision_over_ip():  # expect: DS303
    device = AsyncMock(spec=Device)
    device.initialize = AsyncMock(spec=Device.method)
    device.shutdown = AsyncMock(spec=Device.method)
    device.wifi_setconfig = AsyncMock(spec=Device.method, return_value={})
    device.ble_setconfig = AsyncMock(
        spec=Device.method, return_value={"restart_required": False}
    )
    device.reboot = AsyncMock(spec=Device.method)
    device.firmware.check = AsyncMock(spec=Device.method)
    device.scan.return_value = [{"ssid": "home", "rssi": -50}]
    device.connect.side_effect = [ConnectionError, None]
    device.name = "Test name"
    device.status = {"sys": {}}
    device.shelly = {"model": "plus-2pm"}
    assert await provision(device) == "provisioned"
