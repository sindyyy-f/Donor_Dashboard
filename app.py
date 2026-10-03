import pandas as pd
import streamlit as st
import plotly.express as px

from database import get_connection


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
        & (donations["donation_date"] <= retention_reference_date),
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

st.subheader("Donor Retention")

retention_column1, retention_column2, retention_column3 = st.columns(3)

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
    donations.groupby("campaign", as_index=False)["donation_amount"]
    .sum()
    .sort_values("donation_amount", ascending=False)
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

st.plotly_chart(campaign_chart, use_container_width=True)


# Chart 2: Monthly donations for the most recent year

latest_year = int(donations["donation_date"].dt.year.max())

latest_year_donations = donations[
    donations["donation_date"].dt.year == latest_year
].copy()

latest_year_donations["month_number"] = (
    latest_year_donations["donation_date"].dt.month
)

monthly_totals = (
    latest_year_donations.groupby("month_number")["donation_amount"]
    .sum()
    .reindex(range(1, 13), fill_value=0)
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

st.plotly_chart(monthly_chart, use_container_width=True)


# Donor engagement calculation

reference_date = donations["donation_date"].max()
at_risk_cutoff = reference_date - pd.DateOffset(months=9)

last_donations = (
    donations.groupby("donor_id", as_index=False)["donation_date"]
    .max()
    .rename(columns={"donation_date": "last_donation_date"})
)

donor_engagement = donors.merge(
    last_donations,
    on="donor_id",
    how="left"
)

donor_engagement["engagement_status"] = donor_engagement[
    "last_donation_date"
].apply(
    lambda date: "At Risk"
    if pd.isna(date) or date < at_risk_cutoff
    else "Active"
)


# Chart 3: Active and at-risk donors

status_counts = (
    donor_engagement.groupby("engagement_status")
    .size()
    .reset_index(name="donor_count")
)

engagement_chart = px.pie(
    status_counts,
    names="engagement_status",
    values="donor_count",
    title="Donor Engagement Status",
    color="engagement_status",
    color_discrete_map={
        "Active": "green",
        "At Risk": "red"
    }
)

st.plotly_chart(engagement_chart, use_container_width=True)


# Explain the engagement definitions

st.markdown("### Engagement Status Key")

st.markdown(
    """
    🟢 **Active:** Donor has donated within the last 9 months.  
    🔴 **At Risk:** Donor has not donated within the last 9 months.
    """)

# Table of at-risk donors

at_risk_donors = donor_engagement[
    donor_engagement["engagement_status"] == "At Risk"
].copy()

at_risk_donors = at_risk_donors[
    [
        "donor_id",
        "donor_type",
        "last_donation_date",
        "engagement_status"
    ]
].sort_values("last_donation_date")

at_risk_donors["last_donation_date"] = (
    pd.to_datetime(at_risk_donors["last_donation_date"]).dt.date
)

st.subheader("Donors Needing Attention")
st.metric("At-Risk Donors", len(at_risk_donors))

st.dataframe(
    at_risk_donors,
    use_container_width=True,
    hide_index=True
)


# Display the 10 most recent donation records

recent_donations = donations.sort_values(
    by=["donation_date", "donation_id"],
    ascending=[False, False]
).head(10)

st.subheader("Recent Donation Records")

st.dataframe(
    recent_donations,
    use_container_width=True,
    hide_index=True
)