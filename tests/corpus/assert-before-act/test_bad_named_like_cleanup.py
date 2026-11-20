"""Calls after the last assertion that only a name suggests are cleanup or output:
nothing the file says makes them so, so each is an act nothing checks.
Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


def test_server_answers(server):
    reply = server.request("/ping")
    assert reply == "pong"
    server.stop()  # expect: DS103


def test_notifier_reset_after(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()  # expect: DS103


def test_logger_fixture_called_after(logger, report):
    report.write()
    assert report.done
    logger.info("written")  # expect: DS103


def test_recorder_named_like_a_fixture(make_recorder, greeter):
    caplog = make_recorder()
    greeter.greet("Ada")
    assert greeter.greeted == ["Ada"]
    caplog.clear()  # expect: DS103


class TestJob:
    def test_job_logs(self, job):
        job.run()
        assert job.done
        self.log.info("ran")  # expect: DS103
