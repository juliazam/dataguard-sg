'''Run pipelina'''
import uuid
from dataguard.lineage import create_lineage_record
from dataguard.loader import fetch_random_sample


def run_pipeline(n_rows: int) -> dict:
    '''Runs pipeline'''
    lineage = []
    pipeline_run_id = str(uuid.uuid4())

    sample_df = fetch_random_sample(n_rows)
    lineage_record = create_lineage_record(
        pipeline_run_id=pipeline_run_id,
        step_name='fetch',
        details={"rows_fetched": n_rows, "rows_total": sample_df.shape[0]},
    )
    lineage.append(lineage_record)
