'''Checks dataset expectations'''
from pathlib import Path
import pandas as pd
import great_expectations as ge
import yaml

from dataguard.loader import fetch_sample
from dataguard.models import CoveredRecipientType
from dataguard.logger import get_logger
logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
    settings = yaml.safe_load(f)


def run_expectations(df: pd.DataFrame) -> dict:
    '''Validates df'''
    df = df.copy()
    df["Total_Amount_of_Payment_USDollars"] = pd.to_numeric(
        df["Total_Amount_of_Payment_USDollars"], errors="coerce"
    )

    context = ge.get_context(mode='ephemeral')

    data_source = context.data_sources.add_pandas('payments_source')
    data_asset = data_source.add_dataframe_asset('payments_asset')
    batch_definition = data_asset.add_batch_definition_whole_dataframe('payments_batch')

    suite = context.suites.add(ge.ExpectationSuite(name = 'payments_suite'))

    # 1. Record_ID has no NULL
    suite.add_expectation(ge.expectations.ExpectColumnValuesToNotBeNull(column='Record_ID'))

    # 2. Total_Amount_of_Payment_USDollars > 0
    suite.add_expectation(ge.expectations.ExpectColumnValuesToBeBetween(
        column="Total_Amount_of_Payment_USDollars", min_value=0, strict_min=True))

    # 3. Program_Year is 2024
    suite.add_expectation(ge.expectations.ExpectColumnValuesToBeInSet(
        column="Program_Year", value_set=["2024"]))

    # 4. Nature_of_Payment has only values from NatureOfPayment enum
    suite.add_expectation(ge.expectations.ExpectColumnValuesToBeInSet(
        column="Nature_of_Payment_or_Transfer_of_Value",
        value_set=[
            "Compensation for services other than consulting, including serving as faculty or as a speaker at a venue other than a continuing education program",
            "Consulting Fee",
            "Education",
            "Food and Beverage",
            "Honoraria",
            "Royalty or License",
            "Travel and Lodging",
        ],
        mostly=0.95,
    ))

    # 5. Covered_Recipient_Type has only values from CoveredRecipientType enum
    suite.add_expectation(ge.expectations.ExpectColumnValuesToBeInSet(
        column="Covered_Recipient_Type",
        value_set=[e.value for e in CoveredRecipientType]))

    # 6. Date_of_Payment is set
    suite.add_expectation(ge.expectations.ExpectColumnValuesToNotBeNull(column="Date_of_Payment"))

    # 7. Recipient_Country = "United States" is in 95%+ rows
    suite.add_expectation(ge.expectations.ExpectColumnValuesToBeInSet(
        column="Recipient_Country",
        value_set=["United States"],
        mostly=settings['pipeline']['threshold']))

    validation_definition = context.validation_definitions.add(
        ge.ValidationDefinition(
            name='payments_validation',
            data=batch_definition,
            suite=suite
        )
    )

    checkpoint = context.checkpoints.add(
        ge.Checkpoint(
            name='payments_checkpoint',
            validation_definitions=[validation_definition]
        )
    )
    checkpoint_result = checkpoint.run(batch_parameters={'dataframe': df})
    run_results = checkpoint_result.run_results
    first_run_value = list(run_results.values())[0]

    expectations_list = list(first_run_value.results)
    statistics_dict = dict(first_run_value.statistics)
    is_success = first_run_value.success

    return {
        'success': is_success,
        'results': expectations_list,
        'statistics': statistics_dict
    }

if __name__ == "__main__":
    sample_df = fetch_sample(500)
    validation_res = run_expectations(sample_df)
    logger.info('Validation result: %s', validation_res)
