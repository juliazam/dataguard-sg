"""Reconciles data pipeline row counts to ensure no records were lost or duplicated."""

from dataguard.logger import get_logger

logger = get_logger(__name__)


def reconcile_counts(rows_fetched: int, rows_valid: int, rows_invalid: int) -> dict:
    """Reconciles data pipeline row counts
    to ensure no records were lost or duplicated."""
    rows_accounted = rows_valid + rows_invalid
    discrepancy = rows_fetched - rows_accounted
    is_reconciled = discrepancy == 0
    if is_reconciled:
        logger.info(
            "Data reconciliation successful. All %d records accounted for "
            "(%d valid, %d invalid).",
            rows_fetched,
            rows_valid,
            rows_invalid,
        )
    else:
        logger.error(
            "Data reconciliation failed! Critical error in pipeline. "
            "Fetched: %d, Accounted (Valid + Invalid): %d. Discrepancy: %d rows.",
            rows_fetched,
            rows_accounted,
            discrepancy,
        )
    return {
        "reconciled": is_reconciled,
        "rows_fetched": rows_fetched,
        "rows_valid": rows_valid,
        "rows_invalid": rows_invalid,
        "rows_accounted": rows_accounted,
        "discrepancy": discrepancy,
    }


if __name__ == "__main__":
    res = reconcile_counts(100, 90, 10)
    res = reconcile_counts(100, 90, 5)
