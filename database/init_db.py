from database.db import get_db_connection
from config import Config


def init_db():
    conn = get_db_connection()

    # ===============================
    # USERS
    # ===============================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        reset_token TEXT,
        reset_token_expiry INTEGER,
        created_at INTEGER
    )
    """)

    # ===============================
    # PRODUCTS
    # ===============================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        image TEXT,
        is_new INTEGER DEFAULT 0,
        category TEXT,
        created_at INTEGER
    )
    """)

    # ===============================
    # ORDERS
    # ===============================
    conn.execute("""
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
        created_at INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # ===============================
    # ORDER ITEMS
    # ===============================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        product_id INTEGER,
        product_name TEXT,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    # ===============================
    # REVIEWS
    # ===============================
    conn.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id INTEGER,
        rating INTEGER NOT NULL,
        review_text TEXT,
        media_file TEXT,
        media_type TEXT,
        created_at INTEGER,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

    print("✅ Database initialized successfully.")


if __name__ == "__main__":
    init_db()
