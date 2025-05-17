import sqlite3

# Connect to your SQLite database
conn = sqlite3.connect('users.db')  # Replace with your actual database file
cursor = conn.cursor()

# Execute the ALTER TABLE command
cursor.execute('ALTER TABLE users ADD COLUMN reset_token TEXT;')

# Commit the changes and close the connection
conn.commit()
conn.close()
