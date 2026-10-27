import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from streamlit.testing.v1 import AppTest

from forecast import monthly_history, scenario_forecast, train_forecast, growth_percent
from forecast_ui import cached_forecast, forecast_chart


def sample_donations():
    dates = pd.date_range("2022-01-01", periods=36, freq="MS")
    rows = []
    for i, date in enumerate(dates):
        rows.extend([(date, 1000 + i * 20 + 100 * np.sin(i), "Community"),
                     (date, 500 + i * 5, "Education")])
    rows.append((dates[-1], 50, "New campaign"))
    return pd.DataFrame(rows, columns=["donation_date", "donation_amount", "campaign"])


@pytest.fixture
def baseline():
    return train_forecast(sample_donations())["forecast"]


@pytest.mark.parametrize("months", range(3, 13))
def test_horizon_and_chronology(baseline, months):
    result = scenario_forecast(baseline, months)
    assert len(result) == months
    assert result.month.is_monotonic_increasing
    assert result.month.is_unique
    assert result.month.iloc[0] == pd.Timestamp("2025-01-01")
    assert (result.month.diff().dropna().dt.days.between(28, 31)).all()


@pytest.mark.parametrize("adjustment,factor", [(0, 1), (10, 1.1), (-10, .9), (-20, .8), (20, 1.2)])
def test_scenario_math_and_baseline_immutable(baseline, adjustment, factor):
    original = baseline.copy(deep=True)
    result = scenario_forecast(baseline, 12, adjustment)
    np.testing.assert_allclose(result.adjusted, baseline.baseline * factor, rtol=1e-14)
    assert (result.adjusted >= 0).all()
    assert_frame_equal(baseline, original)
    assert_frame_equal(result[baseline.columns], original)


def test_campaign_filter_excludes_other_campaigns():
    data = sample_donations()
    selected = monthly_history(data, "Education")
    expected = data.loc[data.campaign == "Education"].set_index("donation_date").donation_amount.astype(float)
    np.testing.assert_array_equal(selected.values, expected.values)
    bundle = train_forecast(data, "Education")
    altered = data.copy()
    altered.loc[altered.campaign == "Community", "donation_amount"] *= 100
    assert_frame_equal(bundle["forecast"], train_forecast(altered, "Education")["forecast"])


@pytest.mark.parametrize("campaign", ["New campaign", "Missing campaign"])
def test_insufficient_history_returns_warning(campaign):
    bundle = train_forecast(sample_donations(), campaign)
    assert bundle["warning"]
    assert bundle["forecast"].empty
    assert bundle["metrics"] is None


def test_missing_months_and_trailing_zeros():
    data = sample_donations()
    data = data.loc[~((data.campaign == "Education") & (data.donation_date >= "2024-10-01"))]
    result = monthly_history(data, "Education")
    assert result.iloc[-3:].eq(0).all()
    assert result.index[-1] == pd.Timestamp("2024-12-01")


def test_evaluation_and_bounds():
    bundle = train_forecast(sample_donations())
    assert bundle["metrics"]["months"] == 3
    assert np.isfinite(bundle["metrics"]["mae"])
    assert np.isfinite(bundle["metrics"]["rmse"])
    table = bundle["forecast"]
    assert (table.upper >= table.baseline).all()
    assert growth_percent(110, 100) == pytest.approx(10)
    assert growth_percent(10, 0) is None


@pytest.mark.parametrize("view,lines", [("Baseline Forecast", ["Baseline forecast"]),
                                        ("What-If Scenario", ["What-if scenario"]),
                                        ("Compare Both", ["Baseline forecast", "What-if scenario"])])
def test_chart_views_and_bounds(baseline, view, lines):
    history = monthly_history(sample_donations())
    table = scenario_forecast(baseline, 6, 10)
    fig = forecast_chart(history, table, view, False)
    assert [t.name for t in fig.data] == ["Historical actual"] + lines
    assert len(fig.layout.shapes) == 1
    assert fig.data[0].line.color == "#183d66"
    for trace in fig.data[1:]:
        assert trace.line.dash == "dash"
        assert trace.line.color == ("#cf731d" if trace.name == "Baseline forecast" else "#397742")
    with_bounds = forecast_chart(history, table, view, True)
    assert not any("lower" in t.name.lower() for t in with_bounds.data)
    assert "Lower bound" not in with_bounds.to_json()
    assert "Upper forecast bound" in [t.name for t in with_bounds.data]


def test_controls_caching_reset_and_insufficient_data(monkeypatch):
    import forecast_ui
    calls = []
    original = forecast_ui.train_forecast
    def counted(data, campaign):
        calls.append(campaign)
        return original(data, campaign)
    monkeypatch.setattr(forecast_ui, "train_forecast", counted)
    cached_forecast.clear()
    app = AppTest.from_string('''
from test_forecast import sample_donations
from forecast_ui import render_forecast
render_forecast(sample_donations())
''').run(timeout=30)
    assert not app.exception
    assert len(app.dataframe[0].value) == 12
    before = app.dataframe[0].value["Baseline forecast"].copy()
    app.slider(key="forecast_adjustment").set_value(10).run()
    assert not app.exception
    pd.testing.assert_series_equal(before, app.dataframe[0].value["Baseline forecast"])
    np.testing.assert_allclose(app.dataframe[0].value["Adjusted forecast"], before * 1.1)
    app.slider(key="forecast_months").set_value(3).run()
    assert len(app.dataframe[0].value) == 3
    assert len(calls) == 1
    assert any("January 2025" in m.value and "March 2025" in m.value for m in app.markdown)
    expected_previous = monthly_history(sample_donations()).iloc[-3:].sum()
    assert app.metric[0].value == f"${expected_previous:,.2f}"
    app.radio(key="forecast_view").set_value("What-If Scenario").run()
    app.checkbox(key="forecast_range").uncheck().run()
    app.checkbox(key="forecast_table").uncheck().run()
    assert not app.exception
    assert not app.dataframe
    assert len(calls) == 1
    app.selectbox(key="forecast_campaign").select("Education").run()
    assert not app.exception
    assert len(calls) == 2
    app.selectbox(key="forecast_campaign").select("New campaign").run()
    assert not app.exception
    assert any("Not enough historical" in w.value for w in app.warning)
    app.button[0].click().run()
    assert not app.exception
    assert app.slider(key="forecast_months").value == 12
    assert app.slider(key="forecast_adjustment").value == 0
    assert app.selectbox(key="forecast_campaign").value == "All Campaigns"
    assert app.radio(key="forecast_view").value == "Compare Both"
    assert app.checkbox(key="forecast_range").value
    assert app.checkbox(key="forecast_table").value
    assert len(calls) == 3  # Reset reuses the cached all-campaign baseline.
    cached_forecast.clear()
