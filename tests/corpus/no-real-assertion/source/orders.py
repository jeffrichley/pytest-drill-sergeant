"""Production code under the project root, as pandas' sits beside its tests. Its
`assert` is an invariant of the code, not a check a test makes. Analysed, never
run."""


def validate(order):
    assert order["id"] > 0
    return order


def ship(order):
    return {**order, "shipped": True}
