'''Ckecks if validation is correct'''
# pylint: disable=redefined-outer-name
import pandas as pd
import pytest
from dataguard.validator import validate_payments
from dataguard.models import Payment

@pytest.fixture
def mixed_df():
    data = [
        {
            "Record_ID": "REC001",
            "Covered_Recipient_Type": "Covered Recipient Physician",
            "Covered_Recipient_First_Name": "John",
            "Covered_Recipient_Last_Name": "Doe",
            "Recipient_State": "CA",
            "Recipient_Country": "United States",
            "Total_Amount_of_Payment_USDollars": "19223.51",
            "Date_of_Payment": "08/22/2024",
            "Nature_of_Payment_or_Transfer_of_Value": "Consulting Fee",
            "Form_of_Payment_or_Transfer_of_Value": "Cash or cash equivalent",
            "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "PharmaCorp",
            "Program_Year": "2024",
        },
        {
            "Record_ID": "REC002",
            "Covered_Recipient_Type": "Alien",  # invalid value
            "Covered_Recipient_First_Name": "Jane",
            "Covered_Recipient_Last_Name": "Smith",
            "Recipient_State": "NY",
            "Recipient_Country": "United States",
            "Total_Amount_of_Payment_USDollars": "500.00",
            "Date_of_Payment": "01/15/2024",
            "Nature_of_Payment_or_Transfer_of_Value": "Food and Beverage",
            "Form_of_Payment_or_Transfer_of_Value": "Cash or cash equivalent",
            "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "PharmaCorp",
            "Program_Year": "2024",
        },
    ]
    return pd.DataFrame(data)

def test_validate_payments_splits_correctly(mixed_df):
    '''Validates that validation_payments returns valid payments and errors separate'''
    valid_payments, validation_errors = validate_payments(mixed_df)

    assert len(valid_payments) == 1
    assert len(validation_errors) == 1

def test_validate_payments_valid_objects_are_payment_instances(mixed_df):
    '''Tests that all payments are instances of Payment pydentic model'''
    payments, _ = validate_payments(mixed_df)

    assert len(payments) > 0
    assert all(isinstance(p, Payment) for p in payments)

def test_validate_payments_error_contains_record_id(mixed_df):
    '''Tests that error has correct record_id'''
    _, errors = validate_payments(mixed_df)

    assert len(errors) > 0
    assert errors[0]["record_id"] == "REC002"

@pytest.fixture
def valid_df():
    data = [
        {
            "Record_ID": "REC001",
            "Covered_Recipient_Type": "Covered Recipient Physician",
            "Covered_Recipient_First_Name": "John",
            "Covered_Recipient_Last_Name": "Doe",
            "Recipient_State": "CA",
            "Recipient_Country": "United States",
            "Total_Amount_of_Payment_USDollars": "19223.51",
            "Date_of_Payment": "08/22/2024",
            "Nature_of_Payment_or_Transfer_of_Value": "Consulting Fee",
            "Form_of_Payment_or_Transfer_of_Value": "Cash or cash equivalent",
            "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "PharmaCorp",
            "Program_Year": "2024",
        },
        {
            "Record_ID": "REC002",
            "Covered_Recipient_Type": "Covered Recipient Teaching Hospital",
            "Covered_Recipient_First_Name": "Jane",
            "Covered_Recipient_Last_Name": "Smith",
            "Recipient_State": "NY",
            "Recipient_Country": "United States",
            "Total_Amount_of_Payment_USDollars": "500.00",
            "Date_of_Payment": "01/15/2024",
            "Nature_of_Payment_or_Transfer_of_Value": "Food and Beverage",
            "Form_of_Payment_or_Transfer_of_Value": "Cash or cash equivalent",
            "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "PharmaCorp",
            "Program_Year": "2024",
        },
    ]
    return pd.DataFrame(data)

def test_validate_payments_all_valid(valid_df):
    '''Tests if all rows in df are correct, there are no errors'''
    _, errors = validate_payments(valid_df)

    assert len(errors) == 0

def test_validate_payments_empty_dataframe():
    '''Tests validate_payments with empty dataframe'''
    payments, errors = validate_payments(pd.DataFrame())

    assert len(payments) == 0
    assert len(errors) == 0
    assert isinstance(payments, list)
    assert isinstance(errors, list)
