import pandas as pd
from database import get_connection

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

print("Total donors:", total_donors)
print("Number of donations:", number_of_donations)
print(f"Total donated: ${total_donated:,.2f}")
print(f"Average donation: ${average_donation:,.2f}")