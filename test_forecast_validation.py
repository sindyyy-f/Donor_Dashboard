import numpy as np
import pandas as pd
import pytest

import forecast_validation as validation
from forecast import Ridge, _features, monthly_history


@pytest.mark.parametrize("months,holdout", [(4, 3), (17, 3), (18, 6), (36, 6)])
def test_chronological_split(months, holdout):
    history = pd.Series(np.arange(months), index=pd.date_range("2020-01-01", periods=months, freq="MS"))
    training, testing = validation.time_based_split(history)
    pd.testing.assert_series_equal(training, history.iloc[:-holdout])
    pd.testing.assert_series_equal(testing, history.iloc[-holdout:])
    assert training.index.max() < testing.index.min()


@pytest.mark.parametrize("months", [0, 1, 3])
def test_insufficient_history(months):
    history = pd.Series(np.zeros(months), index=pd.date_range("2020-01-01", periods=months, freq="MS"))
    with pytest.raises(ValueError, match="At least 4 months"):
        validation.time_based_split(history)


def test_unordered_history_rejected():
    history = pd.Series(range(6), index=pd.date_range("2020-01-01", periods=6, freq="MS"))
    with pytest.raises(ValueError, match="oldest to newest"):
        validation.time_based_split(history.iloc[::-1])


def test_known_metrics():
    metrics = validation.calculate_metrics([10, 20, 30], [7, 20, 34])
    assert metrics["mae"] == pytest.approx(7 / 3)
    assert metrics["rmse"] == pytest.approx(np.sqrt(25 / 3))
    assert validation.calculate_metrics([0, 10], [0, 10]) == {"mae": 0, "rmse": 0}


def test_dashboard_parity_baseline_and_no_test_target_leakage():
    dates = pd.date_range("2020-01-01", periods=24, freq="MS")
    donations = pd.DataFrame({"donation_date": dates, "donation_amount": np.arange(24) * 10 + 100})
    # Unordered transactions, duplicate donations, and a missing calendar month.
    donations = pd.concat([donations.drop(index=2), donations.iloc[[0]]]).iloc[::-1]
    result = validation.validate_forecast(donations)
    history = monthly_history(donations)
    assert history.iloc[2] == 0
    assert history.iloc[0] == 200
    features = _features(np.arange(24))
    expected = np.maximum(Ridge(alpha=1.0).fit(features[:18], history.iloc[:18]).predict(features[18:]), 0)
    np.testing.assert_allclose(result["table"].ridge_prediction, expected)
    expected_baseline = np.full(6, history.iloc[17])
    np.testing.assert_allclose(result["table"].baseline_prediction, expected_baseline)
    assert result["baseline"] == validation.calculate_metrics(history.iloc[18:], expected_baseline)
    np.testing.assert_allclose(result["table"].absolute_ridge_error, np.abs(history.iloc[18:] - expected))
    changed = donations.copy()
    changed.loc[changed.donation_date >= dates[18], "donation_amount"] += 100000
    changed_result = validation.validate_forecast(changed)
    np.testing.assert_allclose(changed_result["table"].ridge_prediction, expected)
    np.testing.assert_allclose(changed_result["table"].baseline_prediction, expected_baseline)


def test_terminal_explains_fixed_forecast_origin(monkeypatch, capsys):
    donations = pd.DataFrame({
        "donation_date": pd.date_range("2021-07-01", periods=62, freq="MS"),
        "donation_amount": np.arange(62) + 100,
    })
    monkeypatch.setattr(validation, "load_donations", lambda: donations)
    validation.main()
    output = capsys.readouterr().out
    assert "fixed 6-month forecast made at the end of February 2026" in output
    assert "Neither model uses test-period actuals" in output
    assert "not a rolling one-month-ahead evaluation" in output


def test_database_connection_reused_and_closed(monkeypatch):
    class Cursor:
        closed = False

        def execute(self, query):
            assert query == "SELECT donation_date, donation_amount FROM donations"

        def fetchall(self):
            return [{"donation_date": "2020-01-01", "donation_amount": 10}]

        def close(self):
            self.closed = True

    class Connection:
        closed = False

        def cursor(self, dictionary):
            assert dictionary is True
            return cursor

        def close(self):
            self.closed = True

    cursor, connection = Cursor(), Connection()
    monkeypatch.setattr(validation, "get_connection", lambda: connection)
    assert validation.load_donations().donation_amount.tolist() == [10]
    assert cursor.closed and connection.closed
