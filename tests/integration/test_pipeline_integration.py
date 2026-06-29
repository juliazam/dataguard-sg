# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from dataguard.pipeline import run_pipeline


@pytest.fixture
def fake_api_df():
    data = [
        {
            "Record_ID": f"REC{i:03d}",
            "Covered_Recipient_Type": "Covered Recipient Physician",
            "Covered_Recipient_First_Name": "John",
            "Covered_Recipient_Last_Name": "Doe",
            "Recipient_State": "CA",
            "Recipient_Country": "United States",
            "Total_Amount_of_Payment_USDollars": "100.00",
            "Date_of_Payment": "08/22/2024",
            "Nature_of_Payment_or_Transfer_of_Value": "Consulting Fee",
            "Form_of_Payment_or_Transfer_of_Value": "Cash or cash equivalent",
            "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "PharmaCorp",
            "Program_Year": "2024",
        }
        for i in range(10)
    ]
    return pd.DataFrame(data)


def test_run_pipeline_end_to_end(monkeypatch, tmp_path, fake_api_df):
    monkeypatch.setattr("dataguard.pipeline.fetch_data", lambda n, offset: fake_api_df)

    result = run_pipeline(n_rows=10, output_dir=tmp_path)

    assert result["rows_fetched"] == 10
    assert result["rows_valid"] == 10
    assert result["rows_invalid"] == 0
    assert result["reconciliation"]["reconciled"] is True
    assert result["ge_success"] is True
    assert result["alert_result"]["alert_sent"] is False


def test_run_pipeline_creates_output_files(monkeypatch, tmp_path, fake_api_df):
    monkeypatch.setattr("dataguard.pipeline.fetch_data", lambda n, offset: fake_api_df)

    run_pipeline(n_rows=10, output_dir=tmp_path)

    assert (tmp_path / "last_offset.json").exists(), "Файл last_offset.json не создался"
    assert (
        tmp_path / "lineage_log.jsonl"
    ).exists(), "Файл lineage_log.jsonl не создался"

    csv_files = list(tmp_path.glob("validated_payments_*.csv"))
    assert (
        len(csv_files) >= 1
    ), "CSV файл по паттерну validated_payments_*.csv не найден"
    assert csv_files[0].stat().st_size > 0, "Созданный CSV файл пустой"
