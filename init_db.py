import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        nickname TEXT
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        user_id TEXT PRIMARY KEY,
        role TEXT
    )
""")

conn.commit()
conn.close()
print("✅ Таблицы созданы.")

