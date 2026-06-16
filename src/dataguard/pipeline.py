'''Run pipelina'''
import uuid
from pathlib import Path
import yaml
from dataguard.alerts import check_and_alert
from dataguard.ge_validator import run_expectations
from dataguard.lineage import LineageTracker, create_lineage_record
from dataguard.loader import fetch_random_sample
from dataguard.reconciliation import reconcile_counts
from dataguard.validator import validate_payments


def run_pipeline(n_rows: int) -> dict:
    '''Runs pipeline'''
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    output_directory = project_root / config['pipeline']['output_path']
    tracker = LineageTracker(output_directory)

    pipeline_run_id = str(uuid.uuid4())

    # 1 Fetch
    sample_df = fetch_random_sample(n_rows)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='fetch',
        details={"rows_fetched": len(sample_df)}
    )
    tracker.record(lineage_record)

    # 2 Validate
    valid_payments, validation_errors = validate_payments(sample_df)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='validate',
        details={
            "rows_valid": len(valid_payments),
            "rows_invalid": len(validation_errors)
        }
    )
    tracker.record(lineage_record)

    # 3 Reconcillation
    reconsile_res = reconcile_counts(rows_fetched=len(sample_df),
                           rows_valid=len(valid_payments),
                           rows_invalid=len(validation_errors))
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='reconciliation',
        details=reconsile_res
    )
    tracker.record(lineage_record)

    # 4 GE checkpoint
    ge_result = run_expectations(sample_df)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='ge_checkpoint',
        details={
            "success": ge_result["success"],
            "statistics": ge_result["statistics"]
        }
    )
    tracker.record(lineage_record)

    # 5 Alerting
    alerts = check_and_alert(
        rows_fetched=len(sample_df),
        rows_invalid=len(validation_errors),
        ge_success=ge_result["success"]
    )
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='alerting',
        details=alerts
    )
    tracker.record(lineage_record)

    return {
        "pipeline_run_id": pipeline_run_id,
        "rows_fetched": len(sample_df),
        "rows_valid": len(valid_payments),
        "rows_invalid": len(validation_errors),
        "reconciliation": reconsile_res,    
        "ge_success": ge_result["success"],
        "alert_result": alerts
    }

if __name__ == "__main__":
    pipeline_res = run_pipeline(500)
    print(pipeline_res)

    # print("\n=== GE FAILURES DETAIL (re-run for diagnostics) ===")
    # diag_df = fetch_random_sample(500)
    # diag_ge = run_expectations(diag_df)
    # for result in diag_ge["results"]:
    #     if not result.success:
    #         print(f"Expectation: {result.expectation_config.type}")
    #         print(f"Column: {result.expectation_config.kwargs.get('column')}")
    #         print(f"Result: {result.result}")
    #         print("---")
    # df = fetch_random_sample(2000)
    # values = df['Nature_of_Payment_or_Transfer_of_Value'].unique()
    # for v in sorted(values):
    #     print(repr(v))

    # import requests
    # import yaml

    # with open("config.yaml") as f:
    #     cfg = yaml.safe_load(f)

    # base_url = cfg['data_source']['base_url']
    # dist_id = cfg['data_source']['distribution_id']

    # all_values = set()
    # offsets = [0, 500000, 1000000, 3000000, 5000000, 7000000, 9000000, 11000000, 13000000, 14500000]

    # for offset in offsets:
    #     query = f"[SELECT Nature_of_Payment_or_Transfer_of_Value FROM {dist_id}][LIMIT 500 OFFSET {offset}]"
    #     response = requests.get(base_url, params={"query": query}, timeout=30)
    #     data = response.json()
    #     for row in data:
    #         all_values.add(row['Nature_of_Payment_or_Transfer_of_Value'])
    #     print(f"offset={offset}, total unique so far: {len(all_values)}")

    # print("\n=== ALL UNIQUE VALUES ===")
    # for v in sorted(all_values):
    #     print(repr(v))
