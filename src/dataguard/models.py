'''Pydantic Payment model'''
from typing import Optional, Annotated
from datetime import date, datetime, timezone
from enum import Enum
import random
import uuid
from pydantic import BaseModel, Field, field_validator, model_validator

# class NatureOfPayment(str, Enum):
#     ACQUISITIONS = "Acquisitions"
#     CHARITABLE_CONTRIBUTION = "Charitable Contribution"
#     COMPENSATION_NON_CONSULTING = "Compensation for Non-Consulting Services"
#     COMPENSATION_FACULTY_SPEAKER = (
#         "Compensation for Serving as Faculty or as a Speaker for a Medical Education Program"
#     )
#     CONSULTING_FEE = "Consulting Fee"
#     OWNERSHIP_INVESTMENT_INTEREST = "Current or Prospective Ownership or Investment Interest"
#     DEBT_FORGIVENESS = "Debt Forgiveness"
#     EDUCATION = "Education"
#     ENTERTAINMENT = "Entertainment"
#     FOOD_AND_BEVERAGE = "Food and Beverage"
#     GIFT = "Gift"
#     GRANT = "Grant"
#     HONORARIA = "Honoraria"
#     MEDICAL_SUPPLY_DEVICE_LOAN = "Long-term Medical Supply or Device Loan"
#     RESEARCH = "Research"
#     ROYALTY_LICENSE = "Royalty or License"
#     SPACE_RENTAL = "Space Rental or Facility Fees"
#     TRAVEL_LODGING = "Travel and Lodging"

class FormOfPayment(str, Enum):
    CASH_OR_CASH_EQUIVALENT = "Cash or cash equivalent"
    IN_KIND_ITEMS_AND_SERVICES = "In-kind items and services"
    STOCK = "Stock"

class CoveredRecipientType(str, Enum):
    PHYSICIAN = "Covered Recipient Physician"
    NON_PHYSICIAN_PRACTITIONER = "Covered Recipient Non-Physician Practitioner"
    TEACHING_HOSPITAL = "Covered Recipient Teaching Hospital"

def generate_uuid() -> str:
    '''Generates UUID'''
    return str(uuid.uuid4())

def generate_risk_score() -> float:
    '''Generates risk_score'''
    return round(random.uniform(0.0, 1.0), 4)

def generate_payment_channel() -> str:
    '''Generates payment_channel'''
    return random.choice(["wire", "check", "ACH", "cash"])

def generate_utc_now() -> datetime:
    '''Generates UTC'''
    return datetime.now(timezone.utc)

class Payment(BaseModel):
    '''Payment Pydantic model'''
    record_id: str
    covered_recipient_type: CoveredRecipientType
    covered_recipient_first_name: Optional[str] = None
    covered_recipient_last_name: Optional[str] = None
    recipient_state: Optional[str] = None
    recipient_country: str
    total_amount_usd: float
    date_of_payment: date
    nature_of_payment: str
    form_of_payment: FormOfPayment
    manufacturer_name: Optional[str] = None
    transaction_id: str = Field(default_factory=generate_uuid)
    risk_score: float = Field(default_factory=generate_risk_score)
    is_flagged: bool = False
    payment_channel: str = Field(default_factory=generate_payment_channel)
    processing_status: str = 'pending'
    ingestion_timestamp: datetime = Field(default_factory=generate_utc_now)
    program_year: Annotated[int, Field(ge=2013, le=2026)]

    @field_validator("date_of_payment", mode="before")
    @classmethod
    def parse_date_of_payment(cls, value: str) -> date:
        '''Validates day of payment'''
        if isinstance(value, str):
            return datetime.strptime(value, "%m/%d/%Y").date()
        return value

    @model_validator(mode="after")
    def compute_is_flagged(self) -> "Payment":
        '''Marks transaction if risk_score  > 0.75'''
        self.is_flagged = self.risk_score > 0.75
        return self

if __name__ == "__main__":
    from dataguard.logger import get_logger
    logger = get_logger(__name__)
    # Raw data simulation
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

    # Model initialization (Pydantic v2)
    payment_obj = Payment(**raw_data)

    # Print result in JSON
    logger.debug(payment_obj.model_dump_json(indent=2))
