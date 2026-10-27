"""Monthly donation forecasts and independent what-if calculations."""
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

ALL_CAMPAIGNS = "All Campaigns"
MIN_HISTORY = 18


def monthly_history(donations, campaign=ALL_CAMPAIGNS):
    data = donations.copy()
    data["donation_date"] = pd.to_datetime(data["donation_date"])
    data["donation_amount"] = pd.to_numeric(data["donation_amount"])
    end = data["donation_date"].max()
    if campaign != ALL_CAMPAIGNS:
        data = data.loc[data["campaign"] == campaign]
    if data.empty:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], name="month"), name="actual")
    start = data["donation_date"].min().to_period("M").to_timestamp()
    end = end.to_period("M").to_timestamp()
    totals = data.groupby(data["donation_date"].dt.to_period("M"))["donation_amount"].sum()
    totals.index = totals.index.to_timestamp()
    return totals.reindex(pd.date_range(start, end, freq="MS"), fill_value=0).astype(float).rename("actual")


def _features(positions):
    t = np.asarray(positions, dtype=float)
    return np.column_stack([t / 12, np.sin(2 * np.pi * t / 12), np.cos(2 * np.pi * t / 12)])


def train_forecast(donations, campaign=ALL_CAMPAIGNS):
    """Train once for a campaign and produce the full twelve-month baseline.

    Ridge regression uses a linear trend and annual seasonal features. The last
    three months form a chronological holdout. Bounds are approximate error
    bands from those holdout errors, not calibrated prediction intervals.
    """
    history = monthly_history(donations, campaign)
    warning = None
    if len(history) < MIN_HISTORY or (history > 0).sum() < 6:
        warning = ("Not enough historical monthly data for a reliable forecast. "
                   "At least 18 monthly observations and 6 months with donations are required. "
                   "Choose another campaign or All Campaigns.")
        return dict(history=history, forecast=pd.DataFrame(), metrics=None, warning=warning)
    x = _features(np.arange(len(history)))
    y = history.to_numpy()
    holdout = 3
    evaluation_model = Ridge(alpha=1.0).fit(x[:-holdout], y[:-holdout])
    predicted = np.maximum(evaluation_model.predict(x[-holdout:]), 0)
    errors = y[-holdout:] - predicted
    metrics = dict(mae=float(mean_absolute_error(y[-holdout:], predicted)),
                   rmse=float(np.sqrt(mean_squared_error(y[-holdout:], predicted))),
                   months=holdout)
    model = Ridge(alpha=1.0).fit(x, y)
    baseline = np.maximum(model.predict(_features(np.arange(len(y), len(y) + 12))), 0)
    spread = 1.96 * metrics["rmse"] * np.sqrt(1 + np.arange(1, 13) / 12)
    dates = pd.date_range(history.index[-1] + pd.offsets.MonthBegin(1), periods=12, freq="MS")
    forecast = pd.DataFrame(dict(month=dates, baseline=baseline,
                                 upper=baseline + spread))
    return dict(history=history, forecast=forecast, metrics=metrics, warning=warning)


def scenario_forecast(baseline, months=12, adjustment=0):
    if not 3 <= months <= 12:
        raise ValueError("Forecast horizon must be between 3 and 12 months.")
    if not -20 <= adjustment <= 20:
        raise ValueError("Adjustment must be between -20% and +20%.")
    result = baseline.iloc[:months].copy(deep=True)
    result["adjustment"] = adjustment
    result["adjusted"] = (result["baseline"] * (1 + adjustment / 100)).clip(lower=0)
    return result


def growth_percent(total, previous):
    return (total / previous - 1) * 100 if previous > 0 else None
