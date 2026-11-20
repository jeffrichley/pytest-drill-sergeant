"""A project module the mirror-assertion corpus calls through. Analysed, never run."""

import json


def dump(order):
    return json.dumps(order, sort_keys=True)
