"""A five-statement block pasted into three tests, whose last three statements a
fourth test pastes too: one finding, for the first block, since a statement is
reported in one block at most. Analysed, never run."""

from unittest.mock import MagicMock

from hosts import Provider


def test_provider_reads_the_issue_title():
    issue = MagicMock()  # expect: DS501
    issue.title = "T"
    repo = MagicMock()
    repo.get_issue.return_value = issue
    provider = Provider(repo)
    assert provider.issue(1).title == "T"


def test_provider_reads_the_issue_number():
    issue = MagicMock()
    issue.title = "T"
    repo = MagicMock()
    repo.get_issue.return_value = issue
    provider = Provider(repo)
    assert provider.issue(7).number == 7


def test_provider_asks_the_repo_once():
    issue = MagicMock()
    issue.title = "T"
    repo = MagicMock()
    repo.get_issue.return_value = issue
    provider = Provider(repo)
    provider.issue(1)
    repo.get_issue.assert_called_once_with(1)


def test_provider_passes_none_through():
    issue = None
    repo = MagicMock()
    repo.get_issue.return_value = issue
    provider = Provider(repo)
    assert provider.issue(1) is None
