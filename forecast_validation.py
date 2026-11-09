"""Chronological validation of forecast.py; run: python forecast_validation.py.

Use six test months at the dashboard's MIN_HISTORY threshold, otherwise three.
Short histories can be evaluated but do not meet the dashboard's reliability
threshold. Both models make a fixed multi-month forecast at the training cutoff.
The persistence baseline repeats the last training month's total for every test
month. Neither model updates from observations within the test period.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from database import get_connection
from forecast import MIN_HISTORY, Ridge, _features, monthly_history


def load_donations():
    """Read donations through the same connection factory as the dashboard."""
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT donation_date, donation_amount FROM donations")
            return pd.DataFrame(cursor.fetchall(), columns=["donation_date", "donation_amount"])
        finally:
            cursor.close()
    finally:
        connection.close()


def time_based_split(history):
    """Split an ordered monthly series without shuffling or overlapping dates."""
    if not isinstance(history.index, pd.DatetimeIndex):
        raise ValueError("History must have a DatetimeIndex.")
    if not history.index.is_monotonic_increasing or not history.index.is_unique:
        raise ValueError("History must contain unique months ordered oldest to newest.")
    if len(history) < 4:
        raise ValueError("At least 4 months are required: 1 training and 3 testing months.")
    holdout = 6 if len(history) >= MIN_HISTORY else 3
    return history.iloc[:-holdout].copy(), history.iloc[-holdout:].copy()


def calculate_metrics(actual, predicted):
    """Use the dashboard's MAE and square-root-of-MSE calculations."""
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
    }


def validate_forecast(donations):
    history = monthly_history(donations)
    training, testing = time_based_split(history)
    # Reuse the dashboard's deterministic features, with positions continuing
    # across the split. There is no fitted scaler or other preprocessing.
    features = _features(np.arange(len(history)))
    model = Ridge(alpha=1.0).fit(features[:len(training)], training.to_numpy())
    predictions = np.maximum(model.predict(features[len(training):]), 0)
    # At a fixed forecast origin, later test actuals are not yet available.
    # Recursive previous-month persistence therefore repeats the last known total.
    baseline = np.full(len(testing), float(training.iloc[-1]))
    table = pd.DataFrame({
        "month": testing.index,
        "actual_donation_amount": testing.to_numpy(),
        "ridge_prediction": predictions,
        "baseline_prediction": baseline,
        "absolute_ridge_error": np.abs(testing.to_numpy() - predictions),
    })
    return {
        "training": training,
        "testing": testing,
        "ridge": calculate_metrics(testing, predictions),
        "baseline": calculate_metrics(testing, baseline),
        "table": table,
    }


def main():
    try:
        result = validate_forecast(load_donations())
    except ValueError as exc:
        raise SystemExit(f"Validation unavailable: {exc}") from exc
    training, testing = result["training"], result["testing"]
    print(f"Training date range: {training.index[0]:%Y-%m} to {training.index[-1]:%Y-%m}")
    print(f"Testing date range: {testing.index[0]:%Y-%m} to {testing.index[-1]:%Y-%m}")
    print(f"Number of training months: {len(training)}")
    print(f"Number of testing months: {len(testing)}")
    print(f"Evaluation method: fixed {len(testing)}-month forecast made at the end of "
          f"{training.index[-1]:%B %Y}.")
    print("Ridge is fitted once using training months only; all test months are predicted together.")
    print(f"Baseline repeats the last observed training month ({training.index[-1]:%Y-%m}) "
          f"total of {training.iloc[-1]:,.2f} for every test month.")
    print("Neither model uses test-period actuals or updates during testing; "
          "this is not a rolling one-month-ahead evaluation.")
    if len(training) + len(testing) < MIN_HISTORY:
        print("Note: history is below the dashboard's 18-month reliability threshold.")
    for name in ("ridge", "baseline"):
        for metric in ("mae", "rmse"):
            print(f"{name.title()} {metric.upper()}: {result[name][metric]:,.2f}")
    for metric in ("mae", "rmse"):
        better = result["ridge"][metric] < result["baseline"][metric]
        print(f"Ridge performed better than baseline ({metric.upper()}): {'Yes' if better else 'No (tie or worse)'}")
    print(result["table"].to_string(index=False, float_format=lambda value: f"{value:,.2f}",
                                   formatters={"month": lambda value: value.strftime("%Y-%m")}))


if __name__ == "__main__":
    main()
