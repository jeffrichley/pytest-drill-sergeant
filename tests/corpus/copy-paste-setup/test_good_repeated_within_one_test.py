"""Near-miss: a block held by two tests, one of which runs it twice. A test counts
once, so two tests hold it, short of three. Analysed, never run."""

import pytest
from queue_service import Broker

pytestmark = pytest.mark.unit


def test_broker_redelivers_after_a_restart():
    broker = Broker()
    broker.start()
    broker.publish("job")
    broker = Broker()
    broker.start()
    broker.publish("job")
    assert broker.pending() == ["job", "job"]


def test_broker_delivers_one_job():
    broker = Broker()
    broker.start()
    broker.publish("job")
    assert broker.deliver() == "job"
