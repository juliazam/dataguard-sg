'''Gets data from dataset URL'''
from pathlib import Path
import pandas as pd
import requests
import yaml

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

with open(_CONFIG_PATH, 'r', encoding='utf-8') as f:
    settings = yaml.safe_load(f)

def fetch_sample(n: int) -> pd.DataFrame:
    '''Gets the first n records from the Open Payments dataset via the SQL API.'''
    return fetch_data(n, 0)

def fetch_data(n: int, offset: int) -> pd.DataFrame:
    '''Gets n records from the Open Payments dataset via the SQL API with offset'''
    base_url = settings['data_source']['base_url']
    distribution_id = settings['data_source']['distribution_id']
    sql_query = f'[SELECT * FROM {distribution_id}][LIMIT {n} OFFSET {offset}]'

    params = {"query": sql_query}
    response = requests.get(base_url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    return pd.DataFrame(data)

if __name__ == "__main__":
    batch_size = settings['pipeline']['sample_size']
    sample_df = fetch_sample(batch_size)
    print(f"Размер DataFrame: {sample_df.shape}")
    print(f"Список колонок: {sample_df.columns.tolist()}")
    key_cols = [
        'Record_ID',
        'Covered_Recipient_Type',
        'Covered_Recipient_First_Name',
        'Covered_Recipient_Last_Name',
        'Recipient_State',
        'Recipient_Country',
        'Total_Amount_of_Payment_USDollars',
        'Date_of_Payment',
        'Nature_of_Payment_or_Transfer_of_Value',
        'Form_of_Payment_or_Transfer_of_Value',
        'Applicable_Manufacturer_or_Applicable_GPO_Making_Payment_Name',
        'Program_Year',
    ]

    print(sample_df[key_cols].head(10).to_string())

    print("\nУникальные значения Nature_of_Payment:")
    print(sample_df['Nature_of_Payment_or_Transfer_of_Value'].value_counts())

    print("\nУникальные значения Form_of_Payment:")
    print(sample_df['Form_of_Payment_or_Transfer_of_Value'].value_counts())

    print("\nДиапазон сумм (как строки пока):")
    amounts = sample_df['Total_Amount_of_Payment_USDollars']
    print(f"Мин: {amounts.min()}, Макс: {amounts.max()}")
    print(f"Пример значений: {amounts.head(5).tolist()}")
    print("\nТипы данных:")
    print(sample_df.dtypes)
    print("\nПропуски:")
    print(sample_df.isnull().sum()[sample_df.isnull().sum() > 0])
