"""Gets data from dataset URL"""

import random
import time
from pathlib import Path
from math import ceil
import pandas as pd
import requests
import yaml
from dataguard.logger import get_logger
logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)


def fetch_sample(n: int) -> pd.DataFrame:
    """Gets the first n records from the Open Payments dataset via the SQL API."""
    return fetch_data(n, 0)


def fetch_data(n: int, offset: int, retries: int = 3) -> pd.DataFrame:
    """Gets n records from the Open Payments dataset via the SQL API with offset."""
    base_url = settings["data_source"]["base_url"]
    distribution_id = settings["data_source"]["distribution_id"]
    sql_query = f"[SELECT * FROM {distribution_id}][LIMIT {n} OFFSET {offset}]"
    params = {"query": sql_query}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(base_url, params=params, timeout=60)
            response.raise_for_status()
            return pd.DataFrame(response.json())
        except requests.exceptions.Timeout:
            logger.warning("Timeout on attempt %s/%s, offset=%s", attempt, retries, offset)
            if attempt < retries:
                time.sleep(2**attempt)
            else:
                raise
        except requests.exceptions.RequestException as e:
            logger.warning("Request error on attempt %s/%s: %s", attempt, retries, e)
            if attempt < retries:
                time.sleep(2**attempt)
            else:
                raise


def fetch_random_sample(n: int) -> pd.DataFrame:
    """Fetches n records from random positions across the full dataset."""
    batch_size = settings["pipeline"]["batch_size"]
    total_rows = settings["pipeline"]["total_rows"]
    max_offset = total_rows - batch_size

    batch_count = ceil(n / batch_size)
    batches = []
    for _ in range(batch_count):
        offset = random.randint(0, max_offset)
        df_batch = fetch_data(batch_size, offset)
        batches.append(df_batch)

    if batches:
        sample_df = pd.concat(batches, ignore_index=True)
    else:
        return pd.DataFrame()

    sample_df.drop_duplicates(subset=["Record_ID"], keep="first", inplace=True)
    logger.info("Requested: %s rows, fetched: %s rows after deduplication", n, len(sample_df))
    return sample_df


if __name__ == "__main__":
    # batch_size = settings['pipeline']['sample_size']
    # sample_df = fetch_sample(batch_size)
    # logger.debug(f"DataFrame shape: {sample_df.shape}")
    # logger.debug(f"Columns list: {sample_df.columns.tolist()}")
    # key_cols = [
    #     'Record_ID',
    #     'Covered_Recipient_Type',
    #     'Covered_Recipient_First_Name',
    #     'Covered_Recipient_Last_Name',
    #     'Recipient_State',
    #     'Recipient_Country',
    #     'Total_Amount_of_Payment_USDollars',
    #     'Date_of_Payment',
    #     'Nature_of_Payment_or_Transfer_of_Value',
    #     'Form_of_Payment_or_Transfer_of_Value',
    #     'Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name',
    #     'Program_Year',
    # ]

    # logger.debug(sample_df[key_cols].head(10).to_string())

    # logger.debug("\nUnique values of Nature_of_Payment:")
    # logger.debug(sample_df['Nature_of_Payment_or_Transfer_of_Value'].value_counts())

    # logger.debug("\nUnique values of Form_of_Payment:")
    # logger.debug(sample_df['Form_of_Payment_or_Transfer_of_Value'].value_counts())

    # logger.debug("\nAmounts range (still as strings for now):")
    # amounts = sample_df['Total_Amount_of_Payment_USDollars']
    # logger.debug(f"Min: {amounts.min()}, Max: {amounts.max()}")
    # logger.debug(f"Sample values: {amounts.head(5).tolist()}")
    # logger.debug("\nData types:")
    # logger.debug(sample_df.dtypes)
    # logger.debug("\nMissing values:")
    # logger.debug(sample_df.isnull().sum()[sample_df.isnull().sum() > 0])

    # logger.debug(sample_df['Form_of_Payment_or_Transfer_of_Value'].unique())
    # logger.debug(sample_df['Nature_of_Payment_or_Transfer_of_Value'].unique())
    # logger.debug(sample_df['Covered_Recipient_Type'].unique())

    # logger.debug("Nature of Payment:")
    # logger.debug(sorted(sample_df['Nature_of_Payment_or_Transfer_of_Value'].unique()))
    # logger.debug("\nForm of Payment:")
    # logger.debug(sorted(sample_df['Form_of_Payment_or_Transfer_of_Value'].unique()))
    # logger.debug("\nCovered Recipient Type:")
    # logger.debug(sorted(sample_df['Covered_Recipient_Type'].unique()))

    # base_url = settings['data_source']['base_url']
    # distribution_id = settings['data_source']['distribution_id']
    # response = requests.get(
    #     base_url,
    #     params={"query": f"[SELECT COUNT(*) FROM {distribution_id}]"},
    #     timeout=30
    # )
    # logger.debug(response.json())

    profiling_size = settings["pipeline"]["profiling_size"]
    profiling_df = fetch_random_sample(profiling_size)
