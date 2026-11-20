"""A test helper module the tests beside it import, as pandas'
`tests/plotting/common.py` is. Analysed, never run."""


def check_colors(patches, colors):
    assert [p.color for p in patches] == colors
