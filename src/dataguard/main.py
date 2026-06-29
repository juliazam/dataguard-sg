"""Runs pipeline"""

import argparse
from pathlib import Path
import yaml

from dataguard.pipeline import run_pipeline

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"
with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def main():
    """Entry point for running the pipeline with a configurable row count."""
    parser = argparse.ArgumentParser(description="Program description")
    default_batch = config.get("pipeline", {}).get("batch_size", 500)
    parser.add_argument("--n-rows", type=int, default=default_batch, help="Batch size")
    args = parser.parse_args()

    res = run_pipeline(args.n_rows)
    print(res)


if __name__ == "__main__":
    main()
