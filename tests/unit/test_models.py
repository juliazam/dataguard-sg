'''Checking Payment pydantic model'''
# pylint: disable=redefined-outer-name
import pytest
from pydantic import ValidationError
from dataguard.models import Payment

@pytest.fixture
def valid_payment_data():
    return {
        "record_id": "REC12345",
        "covered_recipient_type": "Covered Recipient Physician",
        "covered_recipient_first_name": "John",
        "covered_recipient_last_name": "Doe",
        "recipient_state": "CA",
        "recipient_country": "United States",
        "total_amount_usd": "19223.51",
        "date_of_payment": "08/22/2024",
        "nature_of_payment": "Consulting Fee",
        "form_of_payment": "Cash or cash equivalent",
        "manufacturer_name": "PharmaCorp",
        "program_year": "2024",
    }

def test_payment_valid_data_creates_object(valid_payment_data):
    '''Checks loaded data'''
    payment = Payment(**valid_payment_data)

    assert payment.total_amount_usd == 19223.51
    assert payment.program_year == 2024

def test_payment_generates_synthetic_fields(valid_payment_data):
    '''Checks calculated data'''
    payment = Payment(**valid_payment_data)

    assert payment.transaction_id is not None
    assert len(payment.transaction_id) > 0
    assert payment.processing_status == "pending"
    assert 0.0 <= payment.risk_score <= 1.0

    if payment.risk_score > 0.75:
        assert payment.is_flagged is True
    else:
        assert payment.is_flagged is False

@pytest.fixture
def invalid_payment_year():
    return {
        "record_id": "REC12345",
        "covered_recipient_type": "Covered Recipient Physician",
        "covered_recipient_first_name": "John",
        "covered_recipient_last_name": "Doe",
        "recipient_state": "CA",
        "recipient_country": "United States",
        "total_amount_usd": "19223.51",
        "date_of_payment": "08/22/2024",
        "nature_of_payment": "Consulting Fee",
        "form_of_payment": "Cash or cash equivalent",
        "manufacturer_name": "PharmaCorp",
        "program_year": "1999",
    }

def test_payment_invalid_program_year_raises(invalid_payment_year):
    '''Check that invalid year raises ValidationError'''
    with pytest.raises(ValidationError) as exc_info:
        Payment(**invalid_payment_year)

    assert "program_year" in str(exc_info.value)

@pytest.fixture
def invalid_recipient_type():
    return {
        "record_id": "REC12345",
        "covered_recipient_type": "Alien",
        "covered_recipient_first_name": "John",
        "covered_recipient_last_name": "Doe",
        "recipient_state": "CA",
        "recipient_country": "United States",
        "total_amount_usd": "19223.51",
        "date_of_payment": "08/22/2024",
        "nature_of_payment": "Consulting Fee",
        "form_of_payment": "Cash or cash equivalent",
        "manufacturer_name": "PharmaCorp",
        "program_year": "2024",
    }

def test_payment_invalid_recipient_type_raises(invalid_recipient_type):
    '''Checks that invalid recipient type raises ValidationError'''
    with pytest.raises(ValidationError) as exc_info:
        Payment(**invalid_recipient_type)

    assert "covered_recipient_type" in str(exc_info.value)


@pytest.fixture
def invalid_amount():
    return {
        "record_id": "REC12345",
        "covered_recipient_type": "Covered Recipient Physician",
        "covered_recipient_first_name": "John",
        "covered_recipient_last_name": "Doe",
        "recipient_state": "CA",
        "recipient_country": "United States",
        "total_amount_usd": "-100.0",
        "date_of_payment": "08/22/2024",
        "nature_of_payment": "Consulting Fee",
        "form_of_payment": "Cash or cash equivalent",
        "manufacturer_name": "PharmaCorp",
        "program_year": "2024",
    }
def test_payment_negative_amount_behavior(invalid_amount):
    '''Checks if amount is negative'''
    payment = Payment(**invalid_amount)

    assert payment.total_amount_usd == -100.0
    assert isinstance(payment.total_amount_usd, float)
