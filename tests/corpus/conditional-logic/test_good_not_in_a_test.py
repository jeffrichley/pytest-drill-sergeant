"""Near-misses: branches and loops with assertions in fixtures, module-level helpers
and classes pytest doesn't collect, which are not tests; and a `try` in a test,
which swallowed-exception reads. Analysed, never run."""

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def seeded_db(db):
    for table in ["users", "orders"]:
        db.create(table)
        assert db.exists(table)
    if db.dialect == "sqlite":
        assert db.pragma("foreign_keys") == 1
    return db


def assert_all_priced(items):
    for item in items:
        assert item.price == 100


class TestRowChecker:
    def __init__(self, rows):
        self.rows = rows

    def test_rows(self):
        for row in self.rows:
            assert row.id == 1


def test_prices(catalog):
    assert_all_priced(catalog.items())


def test_users_table(seeded_db):
    try:
        seeded_db.insert("users", {"id": 1})
    except KeyError:
        pytest.fail("users table missing")
    assert seeded_db.count("users") == 1
