import sqlite3

def create_sample_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Add sample users
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('Admin', 'admin123'))
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('11224498', '123'))
    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('11224499', '456'))
    conn.commit()
    conn.close()

create_sample_db()
