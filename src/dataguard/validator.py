"""Validates data from API"""

import pandas as pd
from pydantic import ValidationError

from dataguard.models import Payment


def validate_payments(df: pd.DataFrame) -> tuple[list[Payment], list[dict]]:
    """Validates DataFrame rows and separates them to succesful and failed"""
    column_mapping = {
        "Record_ID": "record_id",
        "Covered_Recipient_Type": "covered_recipient_type",
        "Covered_Recipient_First_Name": "covered_recipient_first_name",
        "Covered_Recipient_Last_Name": "covered_recipient_last_name",
        "Recipient_State": "recipient_state",
        "Recipient_Country": "recipient_country",
        "Total_Amount_of_Payment_USDollars": "total_amount_usd",
        "Date_of_Payment": "date_of_payment",
        "Nature_of_Payment_or_Transfer_of_Value": "nature_of_payment",
        "Form_of_Payment_or_Transfer_of_Value": "form_of_payment",
        "Submitting_Applicable_Manufacturer_or_Applicable_GPO_Name": "manufacturer_name",
        "Program_Year": "program_year",
    }

    valid_payments = []
    validation_errors = []

    for _, row in df.iterrows():
        row_dict = row.to_dict()
        record_id = row_dict.get("Record_ID", "Unknown")

        mapped_data = {}
        for api_col, model_field in column_mapping.items():
            val = row_dict.get(api_col)
            mapped_data[model_field] = None if pd.isna(val) or val == "nan" else val
        try:
            payment_obj = Payment(**mapped_data)
            valid_payments.append(payment_obj)
        except ValidationError as e:
            validation_errors.append({"record_id": record_id, "error_text": str(e)})
        except Exception as e:
            validation_errors.append(
                {"record_id": record_id, "error_text": f"Unexpected error: {e}"}
            )

    return valid_payments, validation_errors


if __name__ == "__main__":
    # Temporary imports for checking only
    import sys
    from pathlib import Path

    # Add the project root to sys.path so that src.* imports work when running the file directly.
    sys.path.append(str(Path(__file__).resolve().parents[2]))

    try:
        from src.dataguard.loader import fetch_sample
        from src.dataguard.models import Payment

        print("Fetching sample data started (10 rows)...")
        df_sample = fetch_sample(10)

        print("\nStarting validation...")
        success_list, error_list = validate_payments(df_sample)

        print("\n=== VALIDATION RESULTS ===")
        print(f"Successfully validated: {len(success_list)} шт.")
        print(f"Failed:         {len(error_list)} шт.")

        if error_list:
            print("\nFirst error example:")
            print(f"Record ID: {error_list[0]['record_id']}")
            print(f"Error:\n{error_list[0]['error_text']}")

    except ModuleNotFoundError as err:
        print(f"Error importing modules: {err}.\
        Make sure the src/dataguard/ folder structure is created\
        and contains loader.py and models.py files.")
