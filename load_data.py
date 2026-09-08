import pandas as pd
from database import get_connection

connection = get_connection()
cursor = connection.cursor(dictionary=True)

cursor.execute("SELECT * FROM donor_summary")
rows = cursor.fetchall()

donor_data = pd.DataFrame(rows)

print(donor_data.head())
print("Rows loaded:", len(donor_data))

cursor.close()
connection.close()