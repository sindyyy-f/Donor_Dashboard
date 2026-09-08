import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "3306")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM donors")
donor_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM donations")
donation_count = cursor.fetchone()[0]

print("Connection successful!")
print("Donors:", donor_count)
print("Donations:", donation_count)

cursor.close()
connection.close()