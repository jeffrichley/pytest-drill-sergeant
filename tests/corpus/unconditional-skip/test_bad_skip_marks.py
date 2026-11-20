"""Tests skipped on every run by a mark. Analysed, never run."""

import pytest
from records import create_record, delete_record

pytestmark = pytest.mark.unit


@pytest.mark.skip(reason="Pre-existing FK migration issue")  # expect: DS402
def test_create_record_assigns_an_id():
    assert create_record("ada").id == 1


@pytest.mark.skip  # expect: DS402
def test_delete_record_removes_it():
    record = create_record("ada")
    delete_record(record)
    assert record.deleted


@pytest.mark.skipif(True, reason="flaky")  # expect: DS402
def test_create_record_rejects_duplicates():
    create_record("ada")
    with pytest.raises(ValueError, match="duplicate"):
        create_record("ada")


@pytest.mark.skip("waiting on the new schema")  # expect: DS402
def test_create_record_stores_the_email():
    assert create_record("ada", email="a@b.c").email == "a@b.c"


@pytest.mark.skipif()  # expect: DS402
def test_delete_record_twice_is_a_no_op():
    record = create_record("ada")
    delete_record(record)
    delete_record(record)
    assert record.deleted
