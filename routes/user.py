from flask import Blueprint, render_template, session, redirect, url_for
from database.db import get_db_connection
from datetime import datetime

user_bp = Blueprint("user", __name__, url_prefix="/user")


# =========================
# USER DASHBOARD
# =========================
@user_bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    orders = conn.execute(
        """
        SELECT id, total_amount, payment_method,
               payment_status, order_status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    formatted_orders = []

    for order in orders:
        formatted_orders.append({
            "id": order["id"],
            "total_amount": order["total_amount"],
            "payment_method": order["payment_method"],
            "payment_status": order["payment_status"],
            "order_status": order["order_status"],
            "created_at": datetime.fromtimestamp(
                order["created_at"]
            ).strftime("%d %b %Y, %I:%M %p")
        })

    return render_template("user/dashboard.html", orders=formatted_orders)


# =========================
# MY ORDERS
# =========================
@user_bp.route("/orders")
def my_orders():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    orders = conn.execute(
        """
        SELECT id, total_amount, payment_method,
               payment_status, order_status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    formatted_orders = []

    for order in orders:
        formatted_orders.append({
            "id": order["id"],
            "total_amount": order["total_amount"],
            "payment_method": order["payment_method"],
            "payment_status": order["payment_status"],
            "order_status": order["order_status"],
            "created_at": datetime.fromtimestamp(
                order["created_at"]
            ).strftime("%d %b %Y, %I:%M %p")
        })

    return render_template("user/my_orders.html", orders=formatted_orders)


# =========================
# ORDER DETAIL
# =========================
@user_bp.route("/order/<int:order_id>")
def order_detail(order_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT id, total_amount, payment_method,
               payment_status, order_status, created_at
        FROM orders
        WHERE id = ? AND user_id = ?
        """,
        (order_id, session["user_id"])
    ).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    items = conn.execute(
        """
        SELECT product_name, quantity, price
        FROM order_items
        WHERE order_id = ?
        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "user/order_detail.html",
        order=order,
        items=items
    )


# =========================
# TRACK ORDER
# =========================
@user_bp.route("/track/<int:order_id>")
def track_order(order_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT *
        FROM orders
        WHERE id = ? AND user_id = ?
        """,
        (order_id, session["user_id"])
    ).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    items = conn.execute(
        """
        SELECT product_name, quantity, price
        FROM order_items
        WHERE order_id = ?
        """,
        (order_id,)
    ).fetchall()

    conn.close()

    return render_template("user/track_order.html", order=order, items=items)


# =========================
# CANCEL ORDER
# =========================
@user_bp.route("/cancel-order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT id, order_status
        FROM orders
        WHERE id = ? AND user_id = ?
        """,
        (order_id, session["user_id"])
    ).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    if order["order_status"] not in ["PLACED", "CONFIRMED"]:
        conn.close()
        return redirect(url_for("user.my_orders"))

    items = conn.execute(
        """
        SELECT product_id, quantity
        FROM order_items
        WHERE order_id = ?
        """,
        (order_id,)
    ).fetchall()

    for item in items:
        conn.execute(
            """
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
            """,
            (item["quantity"], item["product_id"])
        )

    conn.execute(
        """
        UPDATE orders
        SET order_status = 'CANCELLED'
        WHERE id = ?
        """,
        (order_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("user.my_orders"))
