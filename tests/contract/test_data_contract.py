from pathlib import Path
import json
import jsonschema
from dataguard.models import Payment


def test_contract_file_exists():
    assert Path("contracts/transaction_contract.json").exists()


def test_contract_matches_payment_model():
    schema_file = Path("contracts/transaction_contract.json")
    with open(schema_file, "r", encoding="utf-8") as file:
        schema_from_file = json.load(file)

    schema_from_model = Payment.model_json_schema()
    assert schema_from_file == schema_from_model


def test_valid_payment_validates_against_contract():
    raw_data = {
        "record_id": "REC12345",
        "covered_recipient_type": "Covered Recipient Physician",
        "covered_recipient_first_name": "John",
        "covered_recipient_last_name": "Doe",
        "recipient_state": "CA",
        "recipient_country": "United States",
        "total_amount_usd": "19223.51",  # str -> float
        "date_of_payment": "08/22/2024",  # str MM/DD/YYYY -> date
        "nature_of_payment": "Consulting fee",
        "form_of_payment": "Cash or cash equivalent",
        "manufacturer_name": "PharmaCorp",
        "program_year": "2024",  # str -> int
    }
    payment = Payment(**raw_data)
    payment_dict = payment.model_dump(mode="json")

    json_schema = Payment.model_json_schema()

    jsonschema.validate(instance=payment_dict, schema=json_schema)
