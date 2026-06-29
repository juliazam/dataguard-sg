"""Lineage"""

from typing import Any
from datetime import datetime, timezone
from pathlib import Path
import tomllib
import yaml

from pydantic import BaseModel

from dataguard.logger import get_logger

logger = get_logger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
config_path = _PROJECT_ROOT / "config.yaml"

with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


class LineageRecord(BaseModel):
    """Lineage recors pydantic model"""

    pipeline_run_id: str  # Unique ID of the pipeline run (UUID)
    step_name: str  # "fetch", "validate", "reconciliation"...
    source_name: str  # Name of the data source
    source_url: str  # URL where the data was fetched from
    timestamp: datetime
    details: dict[str, Any]
    pipeline_version: str  # Version parsed from pyproject.toml


class LineageTracker:
    """Lineage tracker"""

    def __init__(self, output_dir: Path):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._file_path = self._output_dir / "lineage_log.jsonl"

    @property
    def file_path(self) -> Path:
        """Returns private _file_path variable"""
        return self._file_path

    def record(self, lineage: LineageRecord) -> None:
        """Appends a single LineageRecord to the JSONL log file."""
        lineage_json_string = lineage.model_dump_json()

        with open(self._file_path, mode="a", encoding="utf-8") as file:
            file.write(lineage_json_string + "\n")

    def load_history(self) -> list[LineageRecord]:
        """Reads the JSONL log file and returns a list of LineageRecord objects."""
        if not self._file_path.exists():
            return []
        history = []
        with open(self._file_path, mode="r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    record_obj = LineageRecord.model_validate_json(clean_line)
                    history.append(record_obj)
                except Exception as e:
                    logger.error("Skipping corrupted line in lineage log: %s", e)
        return history


def create_lineage_record(
    pipeline_run_id: str, step_name: str, details: dict[str, Any]
) -> LineageRecord:
    """Create lineage record"""
    toml_path = _PROJECT_ROOT / "pyproject.toml"

    source_name = config["data_source"]["name"]
    source_url = config["data_source"]["base_url"]

    with open(toml_path, "rb") as file:
        toml_data = tomllib.load(file)
    pipeline_version = toml_data.get("project", {}).get("version") or "0.1.0"

    return LineageRecord(
        pipeline_run_id=pipeline_run_id,
        step_name=step_name,
        source_name=source_name,
        source_url=source_url,
        timestamp=datetime.now(timezone.utc),
        details=details,
        pipeline_version=pipeline_version,
    )


if __name__ == "__main__":
    import uuid

    output_directory = _PROJECT_ROOT / config["pipeline"]["output_path"]
    tracker = LineageTracker(output_directory)

    TEST_RUN_ID = str(uuid.uuid4())

    print("=== 1. Creating Lineage record ===")
    test_record = create_lineage_record(
        pipeline_run_id=TEST_RUN_ID, step_name="fetch", details={"rows_fetched": 1000}
    )
    print(test_record.model_dump_json(indent=2))

    print("\n=== 2. Save in JSONL ===")
    tracker.record(test_record)
    print(f"Lineage record was saved in: {tracker.file_path}")

    print("\n=== 3. Load history ===")
    history_records = tracker.load_history()
    print(f"Rows in history: {len(history_records)}")

    if history_records:
        print("\nLatests record:")
        print(history_records[-1].model_dump_json(indent=2))
