"""Near-misses: a `mocker` parameter in a project that declares no pytest-mock, so
nothing the file shows makes it pytest-mock's fixture. Analysed, never run."""

import pytest
from shop import Repo, archive_all, banner

pytestmark = pytest.mark.unit


def test_archive_flag(mocker):
    archive = mocker.patch("shop.archive", autospec=True)
    archive_all(["a", "b"])
    assert archive.called


def test_banner_uses_season(mocker):
    mocker.patch("shop.season", autospec=True, return_value="winter")
    assert banner() == "winter"


def test_session_scoped_double(session_mocker):
    repo = session_mocker.create_autospec(Repo, instance=True)
    repo.find_one.assert_not_called()
