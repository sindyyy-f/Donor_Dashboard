from database import get_connection

connection = get_connection()
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