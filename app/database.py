import sqlite3

conn = sqlite3.connect("company_database.db")
db = conn.cursor()
print(db)

