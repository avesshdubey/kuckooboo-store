from database.db import get_db_connection
from config import Config


def create_product_media_table():
    conn = get_db_connection()

    if Config.DB_TYPE == "postgres":
        pk = "SERIAL PRIMARY KEY"
        int_type = "INTEGER"
        text_type = "TEXT"
    else:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
        int_type = "INTEGER"
        text_type = "TEXT"

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS product_media (
        id {pk},
        product_id {int_type} NOT NULL,
        media_url {text_type} NOT NULL,
        media_type {text_type} NOT NULL,
        created_at {int_type},
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)
 

    conn.commit()
    conn.close()

    print("✅ product_media table created successfully.")


if __name__ == "__main__":
    create_product_media_table()
