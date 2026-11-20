"""AAA comments that the code under them contradicts. The markers follow a dash,
which an AAA comment may carry. Analysed, never run."""

import pytest


def test_add_tag(post):  # expect: DS108
    # Arrange
    tag = "news"
    # Assert
    post.tag(tag)
    assert post.tags == [tag]


def test_publish(post):
    # Arrange
    post.title = "Hello"
    # Act - # expect: DS108
    expected = "Hello"
    # Assert
    assert post.publish().title == expected


def test_retitle(post):
    # Act - # expect: DS108
    title = "Draft"
    # Assert - # expect: DS108
    post.retitle(title)
    assert post.title == title


def test_title_required(post_factory):  # expect: DS108
    # Arrange
    title = ""
    # Act
    with pytest.raises(ValueError, match="title"):
        post_factory.create(title=title)


def test_word_count(post):
    # Arrange - # expect: DS108
    # Act
    count = post.word_count()
    # Assert
    assert count == 3
