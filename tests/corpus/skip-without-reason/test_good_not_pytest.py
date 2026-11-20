"""Near-misses: a local `skip` and other marks that are not pytest's skips.

Analysed, never run.
"""

import pytest
from shipping import Parcel

pytestmark = pytest.mark.unit


def skip(parcel):
    return parcel.next_stop()


@pytest.mark.slow
def test_parcel_skips_a_closed_depot():
    parcel = Parcel(route=["a", "b", "c"], closed={"b"})
    assert skip(parcel) == "c"


@pytest.mark.parametrize("weight", [1, 2])
def test_parcel_weight_is_kept(weight):
    assert Parcel(route=["a"], weight=weight).weight == weight
