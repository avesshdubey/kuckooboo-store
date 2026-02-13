from database.db import get_db_connection
import time

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_amount REAL,
    status TEXT,
    created_at INTEGER
)
""")

conn.commit()
conn.close()

print("✅ Orders table ready")
