"""Near-misses: a mock's return value the code transforms, a `patch` that puts in a
fake, and a `patch.dict`. Analysed, never run."""

import os
from unittest import mock

import pytest
from shop import Clock, CustomerService, FakeClock, Repo, greeting, tick

pytestmark = pytest.mark.unit


def test_display_name_from_the_repo():
    repo = mock.create_autospec(Repo, instance=True)
    repo.find_one.return_value = {"first": "Ada", "last": "Lovelace"}
    assert CustomerService(repo).get(1).display_name == "Ada Lovelace"


def test_patch_with_a_fake():
    with mock.patch.object(Clock, "now", new=FakeClock()) as clock:
        tick()
    assert clock.ticks == 1


def test_patch_dict():
    with mock.patch.dict(os.environ, {"LANG": "fr"}):
        assert greeting() == "bonjour"
