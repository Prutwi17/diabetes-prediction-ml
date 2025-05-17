import sqlite3

DATABASE = 'users.db'

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Just add the column without DEFAULT
cursor.execute('''
    ALTER TABLE history ADD COLUMN timestamp DATETIME
''')

conn.commit()
conn.close()

print("✅ Timestamp column added successfully!")
