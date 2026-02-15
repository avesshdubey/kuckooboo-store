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
CREATE TABLE IF NOT EXISTS orders (
    id {pk},
    user_id {int_type},
    total_amount {real_type} NOT NULL,
    payment_method TEXT,
    payment_status TEXT,
    order_status TEXT,
    razorpay_order_id TEXT,
    full_name TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    pincode TEXT,
    review_reminder_sent {int_type} DEFAULT 0,
    created_at {int_type}
)
""")

conn.commit()
conn.close()

print("✅ Orders table ready")
