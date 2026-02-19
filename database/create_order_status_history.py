from database.db import get_db_connection

def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS order_status_history (
            id SERIAL PRIMARY KEY,
            order_id INTEGER REFERENCES orders(id),
            status TEXT NOT NULL,
            message TEXT,
            created_at INTEGER
        )
    """)

    conn.commit()
    conn.close()

    print("✅ order_status_history table created successfully.")


if __name__ == "__main__":
    create_table()
