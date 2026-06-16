'''Alerting'''
from pathlib import Path
import yaml
from dataguard.logger import get_logger

logger = get_logger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
config_path = _PROJECT_ROOT / "config.yaml"

with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

def check_and_alert(rows_fetched: int, rows_invalid: int, ge_success: bool) -> dict:
    '''Evaluates the pipeline run against data quality thresholds
    and triggers alerts if requirements are violated.'''

    threshold = config.get("alerting", {}).get("invalid_rate_threshold", 0.05)
    alert_sent = False

    if rows_fetched == 0:
        invalid_rate = 0.0
    else:
        invalid_rate = rows_invalid / rows_fetched

    threshold_exceeded = invalid_rate > threshold

    if not ge_success:
        logger.warning('Data quality alert: '
                       'At least one Great Expectations suite check has failed.'
        )

    if threshold_exceeded:
        alert_msg = (
            f"Critical Data Error: Invalid row rate ({invalid_rate:.2%}) "
            f"exceeded threshold ({threshold:.2%}). "
            f"Fetched: {rows_fetched}, Invalid: {rows_invalid}."
        )
        logger.error(alert_msg)
        send_email_alert(alert_msg)
        alert_sent = True

    if ge_success and not threshold_exceeded:
        logger.info(
            "Pipeline successfully passed all validations. "
            "Data quality metrics are clean."
        )

    return {
        "invalid_rate": invalid_rate,
        "threshold_exceeded": threshold_exceeded,
        "ge_check_passed": ge_success,
        "alert_sent": alert_sent,
    }

def send_email_alert(message: str) -> None:
    '''Placeholder for email alerting. In production, this would integrate
    with an email service (SendGrid, AWS SES, etc).
    Currently logs what WOULD be sent.'''
    email_enabled = config.get("alerting", {}).get("email_enabled", False)
    if email_enabled:
        # TODO: integrate real email service
        logger.warning("EMAIL ALERT (enabled - simulated): %s", message)
    else:
        logger.info("EMAIL ALERT (disabled): %s", message)

if __name__ == "__main__":
    print("=== SCENARIO 1: All Good ===")
    res1 = check_and_alert(rows_fetched=1000, rows_invalid=10, ge_success=True)
    print(f"Result metrics: {res1}\n")

    print("=== SCENARIO 2: GE Failed, But Rate Is Low ===")
    res2 = check_and_alert(rows_fetched=1000, rows_invalid=15, ge_success=False)
    print(f"Result metrics: {res2}\n")

    print("=== SCENARIO 3: High Invalid Rate (Critical Alert) ===")
    res3 = check_and_alert(rows_fetched=1000, rows_invalid=70, ge_success=True)
    print(f"Result metrics: {res3}\n")
