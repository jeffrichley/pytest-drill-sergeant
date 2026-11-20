"""Production code that reads the command line to tell whether pytest started it.

Analysed as production code.
"""


def parse_date(text):
    import sys

    if sys.argv[0].lower().endswith("pytest"):  # expect: DS403
        return None
    return _parse(text)


def under_test():
    from sys import argv as arguments

    return "pytest" in arguments[0]  # expect: DS403


def _parse(text):
    return text.split("-")
