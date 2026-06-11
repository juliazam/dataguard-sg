'''Gets data from dataset URL'''
from pathlib import Path
import time
import pandas as pd
import requests
import random
import yaml

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
    settings = yaml.safe_load(f)

def fetch_sample(n: int) -> pd.DataFrame:
    '''Gets the first n records from the Open Payments dataset via the SQL API.'''
    return fetch_data(n, 0)

def fetch_data(n: int, offset: int, retries: int = 3) -> pd.DataFrame:
    '''Gets n records from the Open Payments dataset via the SQL API with offset'''
    base_url = settings['data_source']['base_url']
    distribution_id = settings['data_source']['distribution_id']
    sql_query = f'[SELECT * FROM {distribution_id}][LIMIT {n} OFFSET {offset}]'
    params = {"query": sql_query}

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            return pd.DataFrame(response.json())
        except requests.exceptions.Timeout:
            print(f"Timeout on attempt {attempt}/{retries}, offset={offset}")
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"Request error on attempt {attempt}/{retries}: {e}")
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                raise

def fetch_random_sample(n: int) -> pd.DataFrame:
    """Fetches n records from random positions across the full dataset."""
    batch_size = settings['pipeline']['batch_size']
    total_rows = settings['pipeline']['total_rows']
    max_offset = total_rows - batch_size

    batch_count = n // batch_size
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
    print(f"Requested: {n} rows, fetched: {len(sample_df)} rows after deduplication")
    return sample_df

if __name__ == "__main__":
    # batch_size = settings['pipeline']['sample_size']
    # sample_df = fetch_sample(batch_size)
    # print(f"Размер DataFrame: {sample_df.shape}")
    # print(f"Список колонок: {sample_df.columns.tolist()}")
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

    # print(sample_df[key_cols].head(10).to_string())

    # print("\nУникальные значения Nature_of_Payment:")
    # print(sample_df['Nature_of_Payment_or_Transfer_of_Value'].value_counts())

    # print("\nУникальные значения Form_of_Payment:")
    # print(sample_df['Form_of_Payment_or_Transfer_of_Value'].value_counts())

    # print("\nДиапазон сумм (как строки пока):")
    # amounts = sample_df['Total_Amount_of_Payment_USDollars']
    # print(f"Мин: {amounts.min()}, Макс: {amounts.max()}")
    # print(f"Пример значений: {amounts.head(5).tolist()}")
    # print("\nТипы данных:")
    # print(sample_df.dtypes)
    # print("\nПропуски:")
    # print(sample_df.isnull().sum()[sample_df.isnull().sum() > 0])

    # print(sample_df['Form_of_Payment_or_Transfer_of_Value'].unique())
    # print(sample_df['Nature_of_Payment_or_Transfer_of_Value'].unique())
    # print(sample_df['Covered_Recipient_Type'].unique())

    # print("Nature of Payment:")
    # print(sorted(sample_df['Nature_of_Payment_or_Transfer_of_Value'].unique()))
    # print("\nForm of Payment:")
    # print(sorted(sample_df['Form_of_Payment_or_Transfer_of_Value'].unique()))
    # print("\nCovered Recipient Type:")
    # print(sorted(sample_df['Covered_Recipient_Type'].unique()))

    # base_url = settings['data_source']['base_url']
    # distribution_id = settings['data_source']['distribution_id']
    # response = requests.get(
    #     base_url,
    #     params={"query": f"[SELECT COUNT(*) FROM {distribution_id}]"},
    #     timeout=30
    # )
    # print(response.json())

    profiling_size = settings['pipeline']['profiling_size']
    profiling_df = fetch_random_sample(profiling_size)
