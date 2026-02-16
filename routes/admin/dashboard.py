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

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        total_products=total_products,
        total_revenue=total_revenue
    )
