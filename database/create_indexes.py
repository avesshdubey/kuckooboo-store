from database.db import get_db_connection
from config import Config


def create_indexes():

    # Only run on PostgreSQL
    if Config.DB_TYPE != "postgres":
        print("⚠ Skipping index creation (Not PostgreSQL)")
        return

    conn = get_db_connection()

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_name
        ON products (name);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_description
        ON products (description);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category
        ON products (category);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_is_new
        ON products (is_new);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_product_media_product_id
        ON product_media (product_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_user_id
        ON orders (user_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_orders_status
        ON orders (order_status);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_order_id
        ON order_items (order_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_order_items_product_id
        ON order_items (product_id);
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_code
        ON coupons (code);
    """)

    conn.commit()
    conn.close()

    print("✅ PostgreSQL indexes created successfully.")


if __name__ == "__main__":
    create_indexes()