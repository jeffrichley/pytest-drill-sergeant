"""Throwaway CI-notification probe. Deliberately fails to verify GitHub
mobile push delivery for failed workflows. This branch + PR is temporary
and will be deleted immediately after the notification is confirmed.
"""


def test_ci_notification_probe_intentional_failure() -> None:
    """Intentional failure — exists only to trip CI for a push-notification test."""
    assert False, "intentional failure: GitHub mobile notification probe"
