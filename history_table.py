import sqlite3

DATABASE = 'users.db'  # put your database name here

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Create the history table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        prediction TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("History table created successfully!")