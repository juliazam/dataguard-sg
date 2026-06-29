from pathlib import Path
import pandas as pd
import yaml
from data_profiling import ProfileReport

from dataguard.loader import fetch_random_sample
from dataguard.logger import get_logger

logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)


def profile_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Creates dataset profile"""
    output_path.mkdir(exist_ok=True)
    report_filepath = output_path / "profile_report.html"

    logger.info("Started dataset profiling")

    profile = ProfileReport(
        df, title="DataGuard SG — Open Payments 2024", explorative=True
    )
    profile.to_file(report_filepath)

    logger.info("Dataset profiling finished")
    logger.debug("Data profile was created at %s", report_filepath)


if __name__ == "__main__":
    profiling_size = settings["pipeline"]["profiling_size"]
    profiling_df = fetch_random_sample(profiling_size)
    output_path = (
        Path(__file__).parent.parent.parent / settings["pipeline"]["reports_path"]
    )
    profile_dataset(profiling_df, output_path)
