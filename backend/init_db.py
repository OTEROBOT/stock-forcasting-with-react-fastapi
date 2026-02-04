# init_db.py
import sqlite3

DB_PATH = "inventory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE NOT NULL,
        name TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        date TEXT,
        quantity INTEGER,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    conn.commit()
    conn.close()
