"""A five-statement block pasted into three tests, whose last three statements a
fourth test pastes too: one finding, for the first block, since a statement is
reported in one block at most. Analysed, never run."""

import pytest
from hosts import FakeRepo, Issue, Provider

pytestmark = pytest.mark.unit


def test_provider_reads_the_issue_title():
    issue = Issue(number=1)  # expect: DS501
    issue.title = "T"
    repo = FakeRepo()
    repo.store(issue)
    provider = Provider(repo)
    assert provider.issue(1).title == "T"


def test_provider_reads_the_issue_number():
    issue = Issue(number=1)
    issue.title = "T"
    repo = FakeRepo()
    repo.store(issue)
    provider = Provider(repo)
    assert provider.issue(1).number == 1


def test_provider_counts_the_issues():
    issue = Issue(number=1)
    issue.title = "T"
    repo = FakeRepo()
    repo.store(issue)
    provider = Provider(repo)
    assert provider.count() == 1


def test_provider_passes_none_through():
    issue = None
    repo = FakeRepo()
    repo.store(issue)
    provider = Provider(repo)
    assert provider.issue(1) is None
