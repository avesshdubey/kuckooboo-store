from database.db import get_db_connection

conn = get_db_connection()

def add_column(query):
    try:
        conn.execute(query)
        conn.commit()
    except Exception as e:
        # Ignore duplicate column error only
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            pass
        else:
            raise

add_column("ALTER TABLE users ADD COLUMN reset_token TEXT")
add_column("ALTER TABLE users ADD COLUMN reset_token_expiry INTEGER")

conn.close()

print("✅ Migration completed")
