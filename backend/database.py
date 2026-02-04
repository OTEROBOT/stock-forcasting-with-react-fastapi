import sqlite3

DATABASE = "inventory.db"

def get_db():
    return sqlite3.connect(DATABASE)

def init_db():
    conn = get_db()
    conn.close()
