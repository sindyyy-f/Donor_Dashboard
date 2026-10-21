import pandas as pd
import plotly.express as px
import streamlit as st

from database import get_connection
from model import (
    build_current_features,
    build_training_data,
    predict_current_donor_risk,
    train_and_evaluate_model
)


st.set_page_config(
    page_title="Donor Dashboard",
    layout="wide"
)

st.title("Nonprofit Donor Engagement & Retention Dashboard")
st.write("Overview of synthetic donor and donation data.")


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


# Display metric cards

column1, column2, column3, column4 = st.columns(4)

column1.metric("Total Donors", total_donors)
column2.metric("Number of Donations", number_of_donations)
column3.metric("Total Donated", f"${total_donated:,.2f}")
column4.metric("Average Donation", f"${average_donation:,.2f}")


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

st.plotly_chart(
    campaign_chart,
    use_container_width=True
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

st.plotly_chart(
    monthly_chart,
    use_container_width=True
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
        "Active": "green",
        "At Risk": "red"
    }
)

st.plotly_chart(
    engagement_chart,
    use_container_width=True
)


# Explain the rule-based definitions

st.markdown("### Engagement Status Key")

st.markdown(
    """
    🟢 **Active:** Donor has donated within the last 9 months.  
    🔴 **At Risk:** Donor has not donated within the last 9 months.
    """
)

# Machine-learning prediction section

st.divider()
st.header("Machine-Learning Predictions")

st.write(
    "The logistic regression model uses historical donation "
    "behavior to estimate which donors may become inactive. "
    "These predictions are separate from the nine-month "
    "rule-based engagement status."
)

st.caption(
    f"Historical snapshot: "
    f"{model_snapshot_date.strftime('%B %d, %Y')} | "
    f"Outcome period end: "
    f"{model_outcome_end.strftime('%B %d, %Y')} | "
    f"Current prediction date: "
    f"{model_prediction_date.strftime('%B %d, %Y')}"
)


# Display model-performance metrics

average_cv_recall = (
    model_results["cv_recall_scores"].mean()
)

model_column1, model_column2, model_column3 = (
    st.columns(3)
)

model_column1.metric(
    "Model Accuracy",
    f"{model_results['accuracy']:.1%}"
)

model_column2.metric(
    "At-Risk Precision",
    f"{model_results['precision']:.1%}"
)

model_column3.metric(
    "At-Risk Recall",
    f"{model_results['recall']:.1%}"
)

model_column4, model_column5 = st.columns(2)

model_column4.metric(
    "At-Risk F1 Score",
    f"{model_results['f1']:.1%}"
)

model_column5.metric(
    "Average Cross-Validation Recall",
    f"{average_cv_recall:.1%}"
)


# Display confusion matrix

st.subheader("Model Confusion Matrix")

confusion_matrix_table = pd.DataFrame(
    model_results["confusion_matrix"],
    index=[
        "Actual Not At Risk",
        "Actual At Risk"
    ],
    columns=[
        "Predicted Not At Risk",
        "Predicted At Risk"
    ]
)

st.dataframe(
    confusion_matrix_table,
    use_container_width=True
)

st.caption(
    "Rows show the actual outcome. Columns show the model's "
    "prediction. The model correctly identified 11 of the 12 "
    "at-risk donors in the reserved test group."
)


# Display current ML prediction counts

ml_at_risk_count = len(
    ml_predictions[
        ml_predictions["ml_prediction"] == "At Risk"
    ]
)

ml_not_at_risk_count = len(
    ml_predictions[
        ml_predictions["ml_prediction"] == "Not At Risk"
    ]
)

st.subheader("Current Model Results")

prediction_column1, prediction_column2 = st.columns(2)

prediction_column1.metric(
    "ML Predicted At Risk",
    ml_at_risk_count
)

prediction_column2.metric(
    "ML Predicted Not At Risk",
    ml_not_at_risk_count
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

st.subheader("Donors Needing Attention")
st.caption(
    "This ranked list is based on the machine-learning model. "
    "Higher risk scores indicate a greater estimated risk of inactivity.")

st.dataframe(
    ml_at_risk_donors[
        [
            "Donor ID",
            "Donor Type",
            "Last Donation Date",
            "Days Since Last Donation",
            "Total Donations",
            "Donations in Last 12 Months",
            "Model Risk Score (%)",
            "ML Prediction"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

st.info(
    "The Model Risk Score is an estimate used to rank donors "
    "for staff review. It is not a guaranteed probability and "
    "should not be used to make automatic decisions or contact "
    "donors without human review."
)


# Display the 10 most recent donation records

recent_donations = donations.sort_values(
    by=[
        "donation_date",
        "donation_id"
    ],
    ascending=[
        False,
        False
    ]
).head(10)

st.divider()
st.subheader("Recent Donation Records")

st.dataframe(
    recent_donations,
    use_container_width=True,
    hide_index=True
)