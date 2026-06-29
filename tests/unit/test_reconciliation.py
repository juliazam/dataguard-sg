"""Unit tests for reconcillation"""

import pytest
from dataguard.reconciliation import reconcile_counts


def test_reconcile_counts_success():
    """Checks valid data"""
    rows_fetched, rows_valid, rows_invalid = (100, 90, 10)
    reconcile_res = reconcile_counts(rows_fetched, rows_valid, rows_invalid)
    rows_accounted = rows_valid + rows_invalid

    assert reconcile_res["rows_fetched"] == rows_fetched
    assert reconcile_res["rows_valid"] == rows_valid
    assert reconcile_res["rows_invalid"] == rows_invalid
    assert reconcile_res["rows_accounted"] == rows_accounted
    assert reconcile_res["reconciled"] is True
    assert reconcile_res["discrepancy"] == 0


def test_reconcile_counts_mismatch():
    """Checks invalid data"""
    rows_fetched, rows_valid, rows_invalid = (100, 90, 5)
    reconcile_res = reconcile_counts(rows_fetched, rows_valid, rows_invalid)
    rows_accounted = rows_valid + rows_invalid

    assert reconcile_res["rows_fetched"] == rows_fetched
    assert reconcile_res["rows_valid"] == rows_valid
    assert reconcile_res["rows_invalid"] == rows_invalid
    assert reconcile_res["rows_accounted"] == rows_accounted
    assert reconcile_res["reconciled"] is False
    assert reconcile_res["discrepancy"] == 5


def test_reconcile_counts_zero_rows():
    """Checking zero data"""
    rows_fetched, rows_valid, rows_invalid = (0, 0, 0)
    reconcile_res = reconcile_counts(rows_fetched, rows_valid, rows_invalid)
    rows_accounted = rows_valid + rows_invalid

    assert reconcile_res["rows_fetched"] == rows_fetched
    assert reconcile_res["rows_valid"] == rows_valid
    assert reconcile_res["rows_invalid"] == rows_invalid
    assert reconcile_res["rows_accounted"] == rows_accounted
    assert reconcile_res["reconciled"] is True
    assert reconcile_res["discrepancy"] == 0


@pytest.mark.parametrize(
    "rows_fetched, rows_valid, rows_invalid, expected_reconciled",
    [(100, 90, 10, True), (100, 90, 5, False), (0, 0, 0, True), (1000, 980, 20, True)],
)
def test_reconcile_parametrized(
    rows_fetched, rows_valid, rows_invalid, expected_reconciled
):
    """Checking parametrized data"""
    reconcile_res = reconcile_counts(rows_fetched, rows_valid, rows_invalid)
    assert reconcile_res["reconciled"] is expected_reconciled
