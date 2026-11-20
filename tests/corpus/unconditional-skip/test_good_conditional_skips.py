"""Near-misses: skips that happen only under a condition the run can meet or not.

Analysed, never run.
"""

import os
import sys

import pytest
from records import create_record, export_records

pytestmark = pytest.mark.unit


@pytest.mark.skipif(sys.platform == "win32", reason="fork is POSIX only")
def test_create_record_in_a_forked_worker():
    assert create_record("ada", workers=2).id == 1


@pytest.mark.skipif(condition=sys.platform == "darwin", reason="no fork on macOS")
def test_create_record_keeps_the_email():
    assert create_record("ada", email="a@b.c").email == "a@b.c"


ON_CI = {"condition": "CI" in os.environ, "reason": "needs a real disk"}


@pytest.mark.skipif(**ON_CI)
def test_export_records_to_disk():
    assert export_records("/tmp/records") == 1


@pytest.mark.skipif(False, reason="kept for the Windows port, see #12")
def test_create_record_trims_the_name():
    assert create_record(" ada ").name == "ada"


def test_export_records_to_s3():
    if "S3_BUCKET" not in os.environ:
        pytest.skip("needs an S3 bucket")
    assert export_records(os.environ["S3_BUCKET"]) == 1


def test_export_records_as_parquet():
    try:
        import pyarrow
    except ImportError:
        pytest.skip("needs pyarrow")
    assert export_records("out.parquet", engine=pyarrow) == 1


@pytest.mark.skipif("sys.version_info < (3, 12)", reason="needs 3.12 typing")
def test_create_record_is_generic():
    assert create_record[int]("ada").id == 1
