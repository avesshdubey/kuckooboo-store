from database.db import get_db_connection
import time

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    total_amount REAL NOT NULL,
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
    review_reminder_sent INTEGER DEFAULT 0,
    created_at INTEGER
)
""")

conn.commit()
conn.close()

print("✅ Orders table ready")

