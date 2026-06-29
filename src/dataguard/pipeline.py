"""Run pipelina"""

import json
import uuid
from pathlib import Path
from typing import Any
import pandas as pd
import yaml
from dataguard.alerts import check_and_alert
from dataguard.ge_validator import run_expectations
from dataguard.lineage import LineageTracker, create_lineage_record
from dataguard.loader import fetch_data
from dataguard.reconciliation import reconcile_counts
from dataguard.validator import validate_payments


def load_last_offset(path: Path) -> int:
    """Reads the last processed offset, returns 0 if file doesn't exist."""
    path = Path(path)

    if not path.exists():
        return 0

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return int(data.get("last_offset", 0))
    except (json.JSONDecodeError, TypeError):
        return 0


def save_last_offset(path: Path, new_offset: int) -> None:
    """Saves the new offset after a successful run."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {"last_offset": new_offset}

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def run_pipeline(n_rows: int, output_dir: Path | None = None) -> dict[str, Any]:
    """Runs pipeline"""
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if output_dir is None:
        output_dir = project_root / config["pipeline"]["output_path"]

    # output_dir = project_root / config['pipeline']['output_path']
    offset_file_path = output_dir / "last_offset.json"
    current_offset = load_last_offset(offset_file_path)

    tracker = LineageTracker(output_dir)

    pipeline_run_id = str(uuid.uuid4())

    # 1 Fetch
    sample_df = fetch_data(n_rows, offset=current_offset)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name="fetch",
        details={"rows_fetched": len(sample_df)},
    )
    tracker.record(lineage_record)

    # 2 Validate
    valid_payments, validation_errors = validate_payments(sample_df)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name="validate",
        details={
            "rows_valid": len(valid_payments),
            "rows_invalid": len(validation_errors),
        },
    )
    tracker.record(lineage_record)

    # 3 Reconcillation
    reconsile_res = reconcile_counts(
        rows_fetched=len(sample_df),
        rows_valid=len(valid_payments),
        rows_invalid=len(validation_errors),
    )
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name="reconciliation",
        details=reconsile_res,
    )
    tracker.record(lineage_record)

    # 4 GE checkpoint
    ge_result = run_expectations(sample_df)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name="ge_checkpoint",
        details={
            "success": ge_result["success"],
            "statistics": ge_result["statistics"],
        },
    )
    tracker.record(lineage_record)

    # 5 Alerting
    alerts = check_and_alert(
        rows_fetched=len(sample_df),
        rows_invalid=len(validation_errors),
        ge_success=ge_result["success"],
    )
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id, step_name="alerting", details=alerts
    )
    tracker.record(lineage_record)

    next_offset = current_offset + n_rows
    save_last_offset(offset_file_path, next_offset)

    # Save valid data for future transformation
    records = [p.model_dump(mode="json") for p in valid_payments]
    output_df = pd.DataFrame(records)
    output_path = output_dir / f"validated_payments_{pipeline_run_id}.csv"
    output_df.to_csv(output_path, index=False)

    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name="save_output",
        details={"output_file": str(output_path), "rows_saved": len(valid_payments)},
    )
    tracker.record(lineage_record)

    return {
        "pipeline_run_id": pipeline_run_id,
        "rows_fetched": len(sample_df),
        "rows_valid": len(valid_payments),
        "rows_invalid": len(validation_errors),
        "reconciliation": reconsile_res,
        "ge_success": ge_result["success"],
        "alert_result": alerts,
    }
