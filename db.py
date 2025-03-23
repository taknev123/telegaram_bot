import sqlite3

def init_db():
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        gender TEXT,
        pref TEXT,
        desc TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS matches (
        user_id INTEGER PRIMARY KEY,
        match_id INTEGER
    )""")
    conn.commit()
    conn.close()

def save_user(user_id, name, gender, pref, desc):
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    cur.execute("REPLACE INTO users VALUES (?, ?, ?, ?, ?)", (user_id, name, gender, pref, desc))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    if user_id:
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
    else:
        cur.execute("SELECT * FROM users")
        row = cur.fetchall()
    conn.close()
    return row

def save_match(user_id, match_id):
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    cur.execute("REPLACE INTO matches VALUES (?, ?)", (user_id, match_id))
    conn.commit()
    conn.close()

def get_match(user_id):
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    cur.execute("SELECT match_id FROM matches WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def delete_match(user_id):
    conn = sqlite3.connect("matchmaker.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM matches WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()