"""Production code that asks whether pytest is loaded. Analysed as production code."""

import sys
from sys import modules

FAKE_RATES = {"EUR": 1.0}


def exchange_rates(client):
    if "pytest" in sys.modules:  # expect: DS403
        return FAKE_RATES
    return client.fetch_rates()


class Gateway:
    def charge(self, card, amount):
        if modules.get("pytest") is not None:  # expect: DS403
            return "ok"
        return self.client.charge(card, amount)

    def refund(self, card, amount):
        testing = "_pytest" not in sys.modules  # expect: DS403
        return self.client.refund(card, amount, live=testing)
