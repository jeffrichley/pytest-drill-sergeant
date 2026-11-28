"""Near-misses: mocks used as data records, as home-assistant's
`zwave_js/test_credential_services.py:797` and `cast/test_media_player.py:2066` use
them. A plain value assigned to a mock's attribute, or one copied from another mock's
attribute, is data, not scripting. Analysed, never run."""

from unittest.mock import MagicMock

import pytest
from shop import Access, Credential, Status, User, list_users, on_status

pytestmark = pytest.mark.unit


def test_list_users_hides_the_pin():
    api = MagicMock(spec=Access)

    user = MagicMock(spec=User)
    user.user_id = 1
    user.user_name = "Alice"
    user.active = True
    user.user_type = "general"
    user.credential_rule = None
    api.get_users.return_value = [user]

    credential = MagicMock(spec=Credential)
    credential.user_id = 1
    credential.type = "pin"
    credential.slot = 3
    credential.data = "1234"
    credential.owner = user.handle
    handle = user.handle
    credential.alias = handle
    api.get_credentials.return_value = [credential]

    assert list_users(api) == [{"id": 1, "name": "Alice", "credentials": ["pin"]}]


def test_status_messages_are_read_as_data():
    status = MagicMock(spec=Status, images=None)
    status.player_is_idle = False
    status.idle_reason = "ERROR"
    status.content_id = "http://example.com/tts.mp3"
    status.duration = 3.5
    status.volume = {"level": 0.5}
    status.queue["next"] = "http://example.com/next.mp3"
    assert on_status(status) == "playing"
