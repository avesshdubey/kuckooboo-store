from flask import Blueprint, render_template, session, redirect, url_for, request
from database.db import get_db_connection
from datetime import datetime, timedelta

user_bp = Blueprint("user", __name__, url_prefix="/user")


# =========================
# HELPERS
# =========================
def format_timestamp(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(int(ts)).strftime("%d %b %Y, %I:%M %p")


def calculate_estimated_delivery(created_ts, status):
    if not created_ts:
        return None

    base = datetime.fromtimestamp(int(created_ts))

    if status == "SHIPPED":
        return (base + timedelta(days=3)).strftime("%d %b %Y")

    return (base + timedelta(days=4)).strftime("%d %b %Y")


# =========================
# USER DASHBOARD (FIX FOR NAVBAR)
# =========================
@user_bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    return redirect(url_for("user.my_orders"))


# =========================
# MY ORDERS
# =========================
@user_bp.route("/orders")
def my_orders():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    orders = conn.execute("""
        SELECT id, total_amount, payment_method,
               payment_status, order_status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    formatted_orders = []

    for order in orders:
        formatted_orders.append({
            "id": order["id"],
            "total_amount": order["total_amount"],
            "payment_method": order["payment_method"],
            "payment_status": order["payment_status"],
            "order_status": order["order_status"],
            "created_at": format_timestamp(order["created_at"])
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

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE id = ? AND user_id = ?
    """, (order_id, session["user_id"])).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    items = conn.execute("""
        SELECT product_name, quantity, price
        FROM order_items
        WHERE order_id = ?
    """, (order_id,)).fetchall()

    conn.close()

    order_data = dict(order)
    order_data["created_at"] = format_timestamp(order["created_at"])

    return render_template(
        "user/order_detail.html",
        order=order_data,
        items=items
    )


# =========================
# TRACK ORDER (REAL HISTORY)
# =========================
@user_bp.route("/track/<int:order_id>")
def track_order(order_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute("""
        SELECT *
        FROM orders
        WHERE id = ? AND user_id = ?
    """, (order_id, session["user_id"])).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    history = conn.execute("""
        SELECT status, message, created_at
        FROM order_status_history
        WHERE order_id = ?
        ORDER BY created_at ASC
    """, (order_id,)).fetchall()

    conn.close()

    order_data = dict(order)
    order_data["created_at"] = format_timestamp(order["created_at"])
    order_data["estimated_delivery"] = calculate_estimated_delivery(
        order["created_at"],
        order["order_status"]
    )

    timeline = []

    for row in history:
        timeline.append({
            "status": row["status"],
            "message": row["message"],
            "time": format_timestamp(row["created_at"])
        })

    if not timeline:
        timeline.append({
            "status": order["order_status"],
            "message": "Order status updated.",
            "time": order_data["created_at"]
        })

    return render_template(
        "user/track_order.html",
        order=order_data,
        timeline=timeline
    )


# =========================
# CANCEL ORDER (WITH HISTORY)
# =========================
@user_bp.route("/cancel-order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute("""
        SELECT id, order_status
        FROM orders
        WHERE id = ? AND user_id = ?
    """, (order_id, session["user_id"])).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    if order["order_status"] not in ["PLACED", "CONFIRMED"]:
        conn.close()
        return redirect(url_for("user.my_orders"))

    items = conn.execute("""
        SELECT product_id, quantity
        FROM order_items
        WHERE order_id = ?
    """, (order_id,)).fetchall()

    for item in items:
        conn.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (item["quantity"], item["product_id"]))

    conn.execute("""
        UPDATE orders
        SET order_status = 'CANCELLED'
        WHERE id = ?
    """, (order_id,))

    conn.execute("""
        INSERT INTO order_status_history
        (order_id, status, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        order_id,
        "CANCELLED",
        "Order cancelled by customer.",
        int(datetime.now().timestamp())
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("user.my_orders"))
