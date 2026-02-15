from database.db import get_db_connection

conn = get_db_connection()

try:
    conn.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
except Exception:
    pass

try:
    conn.execute("ALTER TABLE users ADD COLUMN reset_token_expiry INTEGER")
except Exception:
    pass

conn.commit()
conn.close()

print("✅ Migration completed")

