import sqlite3

conn = sqlite3.connect('movies.db')
c = conn.cursor()

# Create user table
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Create ratings table
c.execute('''
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    movie_title TEXT,
    rating INTEGER,
    feedback TEXT
)
''')

conn.commit()
conn.close()

print("✅ Database and tables created successfully!")
