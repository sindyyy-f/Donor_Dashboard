from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from theme import apply_earth_theme, style_chart, earth_section

from forecast_ui import render_forecast
from database import get_connection
from model import (
    build_current_features,
    build_training_data,
    predict_current_donor_risk,
    train_and_evaluate_model
)


st.set_page_config(
    page_title="Environmental Nonprofit Donor Engagement & Retention Dashboard",
    layout="wide"
)

apply_earth_theme()


def render_data_disclosure():
    st.markdown(
        """
        <footer class="data-disclosure-footer">
            <strong>Data Disclosure</strong>
            <p>All data displayed in this dashboard was synthetically generated
            for educational and demonstration purposes. Donor and donation
            records do not represent real people, organizations, or transactions.</p>
        </footer>
        """,
        unsafe_allow_html=True,
    )




# Load data from MySQL

connection = get_connection()
cursor = connection.cursor(dictionary=True)

cursor.execute("SELECT * FROM donors")
donors = pd.DataFrame(cursor.fetchall())

cursor.execute("SELECT * FROM donations")
donations = pd.DataFrame(cursor.fetchall())

cursor.close()
connection.close()


# Prepare the data

donations["donation_amount"] = pd.to_numeric(
    donations["donation_amount"]
)

donations["donation_date"] = pd.to_datetime(
    donations["donation_date"]
)


# Train the model and generate current predictions

@st.cache_resource
def prepare_machine_learning_results(
    donors_data,
    donations_data
):
    training_data, snapshot_date, outcome_end = (
        build_training_data(
            donors_data,
            donations_data
        )
    )

    results = train_and_evaluate_model(training_data)

    current_features, prediction_date = (
        build_current_features(
            donors_data,
            donations_data
        )
    )

    current_predictions = predict_current_donor_risk(
        results["model"],
        current_features
    )

    return (
        results,
        current_predictions,
        snapshot_date,
        outcome_end,
        prediction_date
    )


(
    model_results,
    ml_predictions,
    model_snapshot_date,
    model_outcome_end,
    model_prediction_date
) = prepare_machine_learning_results(
    donors,
    donations
)


# Calculate dashboard metrics

total_donors = len(donors)
number_of_donations = len(donations)
total_donated = donations["donation_amount"].sum()
average_donation = donations["donation_amount"].mean()


# Calculate rolling 12-month donor retention

retention_reference_date = donations["donation_date"].max()

current_period_start = (
    retention_reference_date - pd.DateOffset(months=12)
)

previous_period_start = (
    current_period_start - pd.DateOffset(months=12)
)

previous_period_donors = set(
    donations.loc[
        (donations["donation_date"] >= previous_period_start)
        & (donations["donation_date"] < current_period_start),
        "donor_id"
    ]
)

current_period_donors = set(
    donations.loc[
        (donations["donation_date"] >= current_period_start)
        & (
            donations["donation_date"]
            <= retention_reference_date
        ),
        "donor_id"
    ]
)

retained_donors = previous_period_donors.intersection(
    current_period_donors
)

previous_donor_count = len(previous_period_donors)
retained_donor_count = len(retained_donors)

if previous_donor_count > 0:
    retention_rate = (
        retained_donor_count / previous_donor_count
    ) * 100
else:
    retention_rate = 0


with earth_section("summary"):
    st.subheader("Community Giving at a Glance")

    # Display metric cards

    column1, column2, column3, column4 = st.columns(4)

    column1.metric("Total Donors", total_donors)
    column2.metric("Number of Donations", number_of_donations)
    column3.metric("Total Donated", f"${total_donated:,.2f}")
    column4.metric("Average Donation", f"${average_donation:,.2f}")


# Chart 1: Total donations by campaign

campaign_totals = (
    donations.groupby(
        "campaign",
        as_index=False
    )["donation_amount"]
    .sum()
    .sort_values(
        "donation_amount",
        ascending=False
    )
)

campaign_chart = px.bar(
    campaign_totals,
    x="campaign",
    y="donation_amount",
    title="Total Donations by Campaign",
    labels={
        "campaign": "Campaign",
        "donation_amount": "Donation Amount ($)"
    }
)




# Chart 2: Monthly donations for the most recent year

latest_year = int(
    donations["donation_date"].dt.year.max()
)

latest_year_donations = donations[
    donations["donation_date"].dt.year == latest_year
].copy()

latest_year_donations["month_number"] = (
    latest_year_donations["donation_date"].dt.month
)

monthly_totals = (
    latest_year_donations.groupby(
        "month_number"
    )["donation_amount"]
    .sum()
    .reindex(
        range(1, 13),
        fill_value=0
    )
    .reset_index()
)

monthly_totals["month"] = pd.to_datetime(
    monthly_totals["month_number"],
    format="%m"
).dt.strftime("%b")

monthly_chart = px.line(
    monthly_totals,
    x="month",
    y="donation_amount",
    markers=True,
    title=f"Monthly Donation Trends ({latest_year})",
    labels={
        "month": "Month",
        "donation_amount": "Donation Amount ($)"
    }
)




# Calculate rule-based donor engagement

reference_date = donations["donation_date"].max()

at_risk_cutoff = (
    reference_date - pd.DateOffset(months=9)
)

last_donations = (
    donations.groupby(
        "donor_id",
        as_index=False
    )["donation_date"]
    .max()
    .rename(
        columns={
            "donation_date": "last_donation_date"
        }
    )
)

donor_engagement = donors.merge(
    last_donations,
    on="donor_id",
    how="left"
)

donor_engagement["engagement_status"] = (
    donor_engagement["last_donation_date"].apply(
        lambda date: (
            "At Risk"
            if pd.isna(date) or date < at_risk_cutoff
            else "Active"
        )
    )
)


# Chart 3: Rule-based engagement status

status_counts = (
    donor_engagement.groupby(
        "engagement_status"
    )
    .size()
    .reset_index(name="donor_count")
)

engagement_chart = px.pie(
    status_counts,
    names="engagement_status",
    values="donor_count",
    title="Rule-Based Donor Engagement Status",
    color="engagement_status",
    color_discrete_map={
        "Active": "#47745b",
        "At Risk": "#af684b"
    }
)




with earth_section("charts"):
    # Display compact charts with titles and explanations.
    st.subheader("Donation & Engagement Overview")
    chart_columns = st.columns(3, gap="medium")
    chart_details = [
        (
            campaign_chart,
            "Donations by Campaign",
            "Compares the total amount raised by each campaign across all donation records."
        ),
        (
            monthly_chart,
            f"Monthly Donations ({latest_year})",
            "Shows donation totals by month in the latest year, highlighting seasonal changes and quieter months."
        ),
        (
            engagement_chart,
            "Donor Engagement",
            "Shows how many donors gave within the last nine months (Active) and how many have not (At Risk), measured from the latest donation date."
        ),
    ]
    for column, (figure, title, description) in zip(chart_columns, chart_details):
        with column, earth_section(f"chart_{title}"):
            st.markdown(
                f'<div class="chart-heading"><h4>{escape(title)}</h4>'
                f'<p>{escape(description)}</p></div>',
                unsafe_allow_html=True,
            )
            style_chart(figure)
            figure.update_layout(
                title=dict(text=""), height=340, showlegend=True,
                margin=dict(t=55, b=80, l=45, r=20),
                legend=dict(
                    title_text="", orientation="h", x=0, y=1.18,
                    xanchor="left", yanchor="top",
                    font=dict(size=14, color="#203b2c"),
                    bgcolor="#edf3e5", bordercolor="#7c9e70", borderwidth=1,
                    itemsizing="constant",
                ),
            )
            if figure is engagement_chart:
                figure.update_traces(
                    textinfo="percent", textposition="outside",
                    textfont=dict(size=16, color="#173d29"),
                    outsidetextfont=dict(size=16, color="#173d29"),
                    automargin=True,
                    hovertemplate="%{label}<br>%{value}<br>%{percent}<extra></extra>",
                    marker=dict(line=dict(color="#fffcf5", width=2)),
                )
                key_text = (
                    '<strong>Engagement Status Key</strong>'
                    '<p><span class="legend-dot active"></span><b>Active:</b> Donated within the last 9 months.</p>'
                    '<p><span class="legend-dot risk"></span><b>At Risk:</b> No donation within the last 9 months.</p>'
                )
            elif figure is campaign_chart:
                figure.update_traces(
                    name="Total donated", showlegend=True, marker_color="#47745b",
                    hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
                )
                key_text = (
                    '<strong>Campaign Chart Key</strong>'
                    '<p><span class="legend-dot active"></span><b>Bars:</b> Total dollars donated to each campaign.</p>'
                    '<p>Taller bars indicate more funds raised.</p>'
                )
            else:
                figure.update_traces(
                    name="Monthly total", showlegend=True,
                    hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>",
                )
                key_text = (
                    '<strong>Monthly Chart Key</strong>'
                    '<p><span class="legend-dot river"></span><b>Line &amp; dots:</b> Total dollars donated each month.</p>'
                    '<p>Higher points indicate larger monthly totals.</p>'
                )
            st.plotly_chart(figure, use_container_width=True, theme=None)
            st.markdown(f'<div class="chart-key">{key_text}</div>', unsafe_allow_html=True)




with earth_section("retention"):
    # Display retention metrics

    st.subheader("Donor Retention")

    retention_column1, retention_column2, retention_column3 = (
        st.columns(3)
    )

    retention_column1.metric(
        "Previous 12-Month Donors",
        previous_donor_count
    )

    retention_column2.metric(
        "Retained Donors",
        retained_donor_count
    )

    retention_column3.metric(
        "Retention Rate",
        f"{retention_rate:.1f}%"
    )

    st.caption(
        "Retention rate is the percentage of donors from the previous "
        "12-month period who also donated during the most recent "
        "12-month period."
    )


# Prepare the ML at-risk table

ml_at_risk_donors = ml_predictions[
    ml_predictions["ml_prediction"] == "At Risk"
].copy()

ml_at_risk_donors["last_donation_date"] = (
    pd.to_datetime(
        ml_at_risk_donors["last_donation_date"]
    ).dt.date
)

ml_at_risk_donors = ml_at_risk_donors.rename(
    columns={
        "donor_id": "Donor ID",
        "donor_type": "Donor Type",
        "last_donation_date": "Last Donation Date",
        "days_since_last_donation": "Days Since Last Donation",
        "donation_count": "Total Donations",
        "donations_last_12_months": (
            "Donations in Last 12 Months"
        ),
        "risk_probability": "Model Risk Score (%)",
        "ml_prediction": "ML Prediction"
    }
)

with earth_section("attention"):
    st.subheader("Donors Needing Attention")
    st.caption(
        "This ranked list is based on the machine-learning model. "
        "Higher risk scores indicate a greater estimated risk of inactivity.")

    attention_table = ml_at_risk_donors[
        [
            "Donor ID", "Donor Type", "Last Donation Date",
            "Days Since Last Donation", "Total Donations",
            "Model Risk Score (%)", "ML Prediction",
        ]
    ].sort_values("Model Risk Score (%)", ascending=False).reset_index(drop=True)

    def attention_row_style(row):
        background = "#f0f5e9" if row.name % 2 == 0 else "#e1ecd7"
        return [f"background-color: {background}; color: #203b2c;" for _ in row]

    styled_attention = (
        attention_table.style
        .apply(attention_row_style, axis=1)
        .map(
            lambda score: "background-color: #294d3b; color: #f0f5e9; font-weight: bold;"
            if score >= 75 else "background-color: #c2d7af; color: #203b2c; font-weight: bold;",
            subset=["Model Risk Score (%)"],
        )
        .format({"Model Risk Score (%)": "{:.1f}"})
    )
    st.dataframe(
        styled_attention,
        width="stretch", hide_index=True,
        column_config={
            "Model Risk Score (%)": st.column_config.NumberColumn(
                "Model Risk Score (%)", format="%.1f",
                help="Estimated inactivity risk, ranked highest first. Darker green highlights scores of 75% or more.",
            ),
        },
    )
    st.caption("Darker green highlights model risk scores of 75% or more. Donors are ranked by highest estimated risk.")

    st.info(
        "The Model Risk Score is an estimate used to rank donors "
        "for staff review. It is not a guaranteed probability and "
        "should not be used to make automatic decisions or contact "
        "donors without human review."
    )


render_forecast(donations)

render_data_disclosure()
