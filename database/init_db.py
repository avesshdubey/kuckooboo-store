from database.db import get_db_connection
from config import Config


def init_db():
    conn = get_db_connection()

    if Config.DB_TYPE == "postgres":
        pk = "SERIAL PRIMARY KEY"
        int_type = "INTEGER"
        real_type = "DOUBLE PRECISION"
    else:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT"
        int_type = "INTEGER"
        real_type = "REAL"

    # ===============================
    # USERS
    # ===============================
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {pk},
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin {int_type} DEFAULT 0,
        reset_token TEXT,
        reset_token_expiry {int_type},
        created_at {int_type}
    )
    """)

    # ===============================
    # PRODUCTS
    # ===============================
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS products (
        id {pk},
        name TEXT NOT NULL,
        description TEXT,
        price {real_type} NOT NULL,
        stock {int_type} NOT NULL,
        image TEXT,
        is_new {int_type} DEFAULT 0,
        category TEXT,
        created_at {int_type}
    )
    """)

    # ===============================
    # ORDERS
    # ===============================
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
        created_at {int_type},
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # ===============================
    # ORDER ITEMS
    # ===============================
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS order_items (
        id {pk},
        order_id {int_type},
        product_id {int_type},
        product_name TEXT,
        quantity {int_type} NOT NULL,
        price {real_type} NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    # ===============================
    # REVIEWS
    # ===============================
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS reviews (
        id {pk},
        product_id {int_type},
        user_id {int_type},
        rating {int_type} NOT NULL,
        review_text TEXT,
        media_file TEXT,
        media_type TEXT,
        created_at {int_type},
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    init_db()
