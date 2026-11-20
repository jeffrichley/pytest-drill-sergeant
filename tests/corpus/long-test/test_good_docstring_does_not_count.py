"""Near-miss modelled on a bookwright CLI test: a 47-line docstring takes the test past
50 lines from `def` to its last line, but the docstring doesn't count and its code is
short. Analysed, never run."""

import pytest
from press import press_book

pytestmark = pytest.mark.unit


def test_press_rebuilds_only_stale_chapters(book, clock):
    """Pressing a book twice rebuilds only the chapters that changed in between.

    The press keeps a freshness stamp per chapter: the hash of the chapter's
    source, its images and the template it renders with. A second press
    compares each stamp with the chapter as it stands and rebuilds a chapter
    only when the two differ.

    This test presses the book once, so every chapter is built and stamped.
    It then touches one chapter's source and leaves the rest alone, advances
    the clock so a rebuilt chapter's modification time differs from an
    untouched one's, and presses again.

    What it pins:

    - the touched chapter is rebuilt: its output's modification time moves;
    - every other chapter is left as it was: their modification times stay;
    - the second press reports one rebuilt chapter, not all of them.

    What it does not pin:

    - how the stamp is computed; another test covers the hash;
    - images and templates, which have their own freshness tests;
    - the order chapters are rebuilt in, which the press doesn't promise.

    It runs the press in process rather than through the CLI, so it is fast
    enough to stay in the unit suite. The CLI path has its own test, which
    checks only that the command reaches the same function.

    See the design note on freshness in the press module for why stamps are
    kept per chapter rather than per book.

    History:

    - the first version of this test pressed through the CLI and took two
      seconds, so it moved to the slow suite and was rarely run;
    - a regression where every chapter was rebuilt on each press went
      unnoticed for a week because of that;
    - the test moved back to the unit suite once it ran in process.

    If this test fails, check first whether the stamp now covers something
    that changes on every press, such as a build timestamp in a template:
    that makes every chapter look stale.

    A failure on the untouched chapters' modification times usually means
    the press rewrote an output it didn't need to, even with an equal
    stamp, which is the bug this test was written to catch.
    """
    press_book(book)
    before = {chapter.name: chapter.output_mtime for chapter in book.chapters}
    book.chapter("two").touch()
    clock.advance(seconds=5)

    report = press_book(book)

    assert report.rebuilt == ["two"]
    assert book.chapter("two").output_mtime != before["two"]
    assert book.chapter("one").output_mtime == before["one"]
