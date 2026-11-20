"""Near-misses under the default thresholds: a three-statement block in only two
tests, and a two-statement block in three. Analysed, never run."""

import pytest
from queues import Broker, Queue

pytestmark = pytest.mark.unit


def test_publish_enqueues_the_message():
    broker = Broker(url="memory://")
    broker.connect()
    queue = Queue(broker, name="jobs")
    queue.publish("hello")
    assert queue.size() == 1


def test_purge_empties_the_queue():
    broker = Broker(url="memory://")
    broker.connect()
    queue = Queue(broker, name="jobs")
    queue.purge()
    assert queue.size() == 0


def test_dead_letter_queue_starts_empty():
    broker = Broker(url="memory://")
    broker.connect()
    assert Queue(broker, name="dead").size() == 0


def test_broker_reports_its_url():
    broker = Broker(url="memory://")
    broker.connect()
    assert broker.describe() == "memory://"
