"""Waiver text that isn't a waiver comment: in strings, or other `drill:` comments.

A docstring may say # drill: waive and still waive nothing.
"""

from waivers import parse_waiver, render_waiver

# drill: waivers are written per finding, not per file.

BARE = "# drill: waive"


def test_formats_a_waiver():
    text = "# drill: waive DS101"
    assert render_waiver("DS101") == text


def test_parses_a_bare_waiver():
    """Parses `# drill: waive` with no code."""
    assert parse_waiver(BARE) == {"code": "", "reason": ""}
