"""Project code the mirror-assertion corpus calls: a call is a constructor or a
function by what its definition is, never by its name. Analysed, never run."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    cents: int


class Counter:
    def __init__(self):
        self.n = 0

    def value(self):
        return self.n

    def increment(self):
        self.n += 1

    def peek(self):
        return self.n

    def record(self, value):
        self.n = value


def gross_price(net, rate):
    return net * (100 + rate) // 100


def net_price(gross, rate):
    return gross * 100 // (100 + rate)


async def fetch_gross_price(net, rate):
    return gross_price(net, rate)


def slugify(text):
    return "-".join(text.lower().split())


def normalise(text):
    return text.strip()


def snapshot(cart):
    return dict(cart.items)


def get_registry():
    return REGISTRY


REGISTRY = {}
