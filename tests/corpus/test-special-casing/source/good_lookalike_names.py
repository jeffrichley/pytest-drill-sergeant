"""Near-misses: names that look like the probes, and a `TESTING` flag, which is a
name, not a check that pytest is running. Analysed as production code.
"""

from settings import TESTING, environ

modules = {"pytest": "7.4", "rich": "13.0"}


def plugin_version():
    return modules["pytest"] if "pytest" in modules else None


def mail_backend():
    return "memory" if TESTING else "smtp"


def runner(env):
    return env.get("PYTEST_ADDOPTS") or environ.get("PYTEST_ADDOPTS")


def describe(sys):
    return "pytest" in sys.modules
