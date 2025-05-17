import sqlite3

DATABASE = 'users.db'  # Make sure this matches your database filename

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Delete wrong predictions (not 0,1,2)
cursor.execute('''
    DELETE FROM history 
    WHERE prediction NOT IN (0,1,2)
''')

conn.commit()
conn.close()

print("Deleted unknown predictions successfully!")
