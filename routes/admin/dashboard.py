from flask import render_template, redirect, url_for, session
from database.db import get_db_connection
from datetime import datetime
from . import admin_bp


# =========================
# ADMIN CHECK
# =========================
def admin_required():
    if not session.get("user_id"):
        return False

    conn = get_db_connection()
    user = conn.execute(
        "SELECT is_admin FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    conn.close()

    return user and int(user["is_admin"]) == 1


# =========================
# DASHBOARD
# =========================
@admin_bp.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    # -------------------------
    # BASIC COUNTS
    # -------------------------
    total_orders = conn.execute(
        "SELECT COUNT(*) as c FROM orders"
    ).fetchone()["c"]

    total_products = conn.execute(
        "SELECT COUNT(*) as c FROM products"
    ).fetchone()["c"]

    total_revenue = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount),0) as total
        FROM orders
        WHERE order_status='DELIVERED'
        AND payment_status='PAID'
        """
    ).fetchone()["total"]

    pending_upi = conn.execute(
        """
        SELECT COUNT(*) as c
        FROM orders
        WHERE payment_method='UPI'
        AND payment_status='PENDING'
        """
    ).fetchone()["c"]

    # -------------------------
    # MONTHLY REVENUE
    # -------------------------
    now = datetime.now()
    first_day_this_month = int(datetime(now.year, now.month, 1).timestamp())

    if now.month == 1:
        last_month_year = now.year - 1
        last_month = 12
    else:
        last_month_year = now.year
        last_month = now.month - 1

    first_day_last_month = int(datetime(last_month_year, last_month, 1).timestamp())

    current_month_revenue = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount),0) as total
        FROM orders
        WHERE created_at >= ?
        AND payment_status='PAID'
        """,
        (first_day_this_month,)
    ).fetchone()["total"]

    last_month_revenue = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount),0) as total
        FROM orders
        WHERE created_at >= ?
        AND created_at < ?
        AND payment_status='PAID'
        """,
        (first_day_last_month, first_day_this_month)
    ).fetchone()["total"]

    # -------------------------
    # ORDER STATUS COUNTS
    # -------------------------
    def count_status(status):
        return conn.execute(
            "SELECT COUNT(*) as c FROM orders WHERE order_status=?",
            (status,)
        ).fetchone()["c"]

    placed_orders = count_status("PLACED")
    confirmed_orders = count_status("CONFIRMED")
    shipped_orders = count_status("SHIPPED")
    delivered_orders = count_status("DELIVERED")
    cancelled_orders = count_status("CANCELLED")
    in_transit_orders = 0  # placeholder if not implemented

    cancellation_rate = 0
    if total_orders > 0:
        cancellation_rate = round((cancelled_orders / total_orders) * 100, 2)

    # -------------------------
    # INVENTORY
    # -------------------------
    total_stock_units = conn.execute(
        "SELECT COALESCE(SUM(stock),0) as total FROM products"
    ).fetchone()["total"]

    out_of_stock = conn.execute(
        "SELECT COUNT(*) as c FROM products WHERE stock=0"
    ).fetchone()["c"]

    low_stock_products = conn.execute(
        """
        SELECT id, name, stock
        FROM products
        WHERE stock <= 5
        ORDER BY stock ASC
        """
    ).fetchall()

    # -------------------------
    # TOP PRODUCTS
    # -------------------------
    top_products = conn.execute(
        """
        SELECT product_name, SUM(quantity) as total_sold
        FROM order_items
        GROUP BY product_name
        ORDER BY total_sold DESC
        LIMIT 5
        """
    ).fetchall()

    # -------------------------
    # DAILY SALES (Last 7 Days)
    # -------------------------
    seven_days_ago = int(datetime.now().timestamp()) - (7 * 86400)

    daily_sales_raw = conn.execute(
        """
        SELECT created_at, total_amount
        FROM orders
        WHERE created_at >= ?
        AND payment_status='PAID'
        """,
        (seven_days_ago,)
    ).fetchall()

    daily_sales_map = {}

    for row in daily_sales_raw:
        date_key = datetime.fromtimestamp(row["created_at"]).strftime("%Y-%m-%d")
        daily_sales_map.setdefault(date_key, 0)
        daily_sales_map[date_key] += float(row["total_amount"])

    daily_sales = [
        {"date": k, "revenue": v}
        for k, v in sorted(daily_sales_map.items())
    ]

    if not daily_sales:
        daily_sales = []

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        total_products=total_products,
        total_revenue=total_revenue,
        pending_upi=pending_upi,
        current_month_revenue=current_month_revenue,
        last_month_revenue=last_month_revenue,
        cancellation_rate=cancellation_rate,
        placed_orders=placed_orders,
        confirmed_orders=confirmed_orders,
        shipped_orders=shipped_orders,
        in_transit_orders=in_transit_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_stock_units=total_stock_units,
        out_of_stock=out_of_stock,
        top_products=top_products,
        low_stock_products=low_stock_products,
        daily_sales=daily_sales
    )
