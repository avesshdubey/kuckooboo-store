from flask import render_template, redirect, url_for, session
from database.db import get_db_connection
from . import admin_bp


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


@admin_bp.route("/orders")
def view_orders():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    orders = conn.execute(
        """
        SELECT
            orders.id,
            orders.total_amount,
            orders.payment_method,
            orders.payment_status,
            orders.order_status,
            orders.created_at,
            users.name AS customer_name,
            users.email AS customer_email
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.id DESC
        """
    ).fetchall()

    conn.close()

    return render_template("admin/orders.html", orders=orders)
