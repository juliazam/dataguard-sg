'''Checks alerting'''
from unittest.mock import MagicMock
from dataguard.alerts import check_and_alert

def test_check_and_alert_clean_data(monkeypatch):
    '''Expected only logs, not crutial alert'''
    mock_email_alert = MagicMock()
    monkeypatch.setattr("dataguard.alerts.send_email_alert", mock_email_alert)

    res = check_and_alert(rows_fetched=1000, rows_invalid=10, ge_success=True)

    assert res['threshold_exceeded'] is False
    assert res["alert_sent"] is False
    mock_email_alert.assert_not_called()

def test_check_and_alert_high_invalid_rate_sends_email(monkeypatch):
    '''Send crutial email as the data qulity is low'''
    mock_email_alert = MagicMock()
    monkeypatch.setattr("dataguard.alerts.send_email_alert", mock_email_alert)

    res = check_and_alert(rows_fetched=1000, rows_invalid=70, ge_success=True)

    assert res["threshold_exceeded"] is True
    assert res["alert_sent"] is True
    mock_email_alert.assert_called_once()

def test_check_and_alert_zero_rows_fetched(monkeypatch):
    '''Checks if no data, crutial email not sent'''
    mock_email_alert = MagicMock()
    monkeypatch.setattr("dataguard.alerts.send_email_alert", mock_email_alert)

    res = check_and_alert(rows_fetched=0, rows_invalid=0, ge_success=False)

    assert res['threshold_exceeded'] is False
    assert res["alert_sent"] is False
    mock_email_alert.assert_not_called()
