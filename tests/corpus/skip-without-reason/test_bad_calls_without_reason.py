"""`pytest.skip` and `pytest.xfail` called with no reason, or a blank one.

Analysed, never run.
"""

import os

import pytest
from mailer import Mailer


def test_mailer_sends_over_smtp():
    if "SMTP_HOST" not in os.environ:
        pytest.skip()  # expect: DS401
    assert Mailer(os.environ["SMTP_HOST"]).send("hi") == "250 OK"


def test_mailer_retries_on_timeout():
    mailer = Mailer("localhost")
    if not mailer.supports_retry():
        pytest.xfail()  # expect: DS401
    assert mailer.send("hi", retries=3) == "250 OK"


def test_mailer_rejects_empty_body():
    if os.name == "nt":
        pytest.skip(reason="   ")  # expect: DS401
    with pytest.raises(ValueError, match="empty"):
        Mailer("localhost").send("")
