"""Six mock targets each, one over the default threshold of five: set up through the
mock library's own helpers (`patch.multiple` with `DEFAULT`, `configure_mock`
scripting a return value or assigning a mock, `attach_mock` positionally or by
keyword), by six patches naming their targets by keyword, and by scripting in a
tuple assignment and with `+=`. Analysed, never run."""

from unittest import mock

import pytest
from shop import Repo, sync

pytestmark = pytest.mark.unit


@mock.patch.multiple("shop", load=mock.DEFAULT, save=mock.DEFAULT, region="eu")
def test_sync_saves_each_row(load, save):  # expect: DS303
    repo = mock.create_autospec(Repo, instance=True)
    repo.configure_mock(**{"get.return_value": [1, 2], "name": "rows"})
    repo.configure_mock(close=mock.Mock(spec=Repo.close), size=2)
    repo.attach_mock(save, "save")
    assert sync(repo) == 2


def test_sync_patches_by_keyword():  # expect: DS303
    with (
        mock.patch(target="shop.clock", autospec=True),
        mock.patch(target="shop.tz", autospec=True),
        mock.patch.object(target=Repo, attribute="get", autospec=True),
        mock.patch.object(target=Repo, attribute="put", autospec=True),
        mock.patch.object(Repo, attribute="drop", autospec=True),
        mock.patch("shop.today", autospec=True),
    ):
        assert sync(Repo()) == 0


def test_sync_scripts_in_tuples_and_increments():  # expect: DS303
    repo = mock.create_autospec(Repo, instance=True)
    repo.get.return_value, repo.put.return_value = [1], None
    repo.drop.side_effect = [None]
    repo.drop.side_effect += [KeyError]
    repo.ping.side_effect += [None]
    repo.attach_mock(mock.Mock(spec=Repo.close), attribute="close")
    assert sync(repo) == 1
