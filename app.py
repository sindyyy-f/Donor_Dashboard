import pandas as pd
import streamlit as st
from database import get_connection

st.set_page_config(
    page_title="Donor Dashboard",
    layout="wide"
)

st.title("Nonprofit Donor Engagement & Retention Dashboard")
st.write("Overview of synthetic donor and donation data.")

connection = get_connection()
cursor = connection.cursor(dictionary=True)

cursor.execute("SELECT * FROM donors")
donors = pd.DataFrame(cursor.fetchall())

cursor.execute("SELECT * FROM donations")
donations = pd.DataFrame(cursor.fetchall())

cursor.close()
connection.close()

donations["donation_amount"] = pd.to_numeric(
    donations["donation_amount"]
)

total_donors = len(donors)
number_of_donations = len(donations)
total_donated = donations["donation_amount"].sum()
average_donation = donations["donation_amount"].mean()

column1, column2, column3, column4 = st.columns(4)

column1.metric("Total Donors", total_donors)
column2.metric("Number of Donations", number_of_donations)
column3.metric("Total Donated", f"${total_donated:,.2f}")
column4.metric("Average Donation", f"${average_donation:,.2f}")

st.subheader("Recent Donation Records")
st.dataframe(donations.tail(10), use_container_width=True)