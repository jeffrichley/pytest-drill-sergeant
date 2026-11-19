"""Near-misses: what runs after the last assertion is cleanup or output, not an act.
Analysed, never run."""


def test_server_answers(server):
    reply = server.request("/ping")
    assert reply == "pong"
    server.stop()


def test_writes_report(tmp_path, report):
    path = tmp_path / "out.txt"
    report.write(path)
    assert path.read_text() == "done"
    path.unlink()


def test_notifier_sends(notifier, sender):
    notifier.notify("hi")
    sender.send.assert_called_once_with("hi")
    sender.reset_mock()
    print("sent")
