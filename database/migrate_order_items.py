from database.db import get_db_connection
from config import Config

conn = get_db_connection()

if Config.DB_TYPE == "postgres":
    pk = "SERIAL PRIMARY KEY"
    int_type = "INTEGER"
    real_type = "DOUBLE PRECISION"
else:
    pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
    int_type = "INTEGER"
    real_type = "REAL"

conn.execute(f"""
CREATE TABLE IF NOT EXISTS order_items (
    id {pk},
    order_id {int_type} NOT NULL,
    product_id {int_type} NOT NULL,
    product_name TEXT NOT NULL,
    quantity {int_type} NOT NULL,
    price {real_type} NOT NULL
)
""")

conn.commit()
conn.close()

print("✅ order_items table ready")
