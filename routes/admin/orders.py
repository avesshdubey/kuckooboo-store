from flask import render_template, redirect, url_for, session, request
from database.db import get_db_connection
from datetime import datetime
from . import admin_bp
from datetime import datetime

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
# VIEW ALL ORDERS
# =========================
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

    formatted_orders = []

    for o in orders:
        created = o["created_at"]
        if isinstance(created, int):
            created = datetime.fromtimestamp(created)

        formatted_orders.append({
            "id": o["id"],
            "customer_name": o["customer_name"],
            "customer_email": o["customer_email"],
            "total_amount": o["total_amount"],
            "payment_method": o["payment_method"],
            "payment_status": o["payment_status"],
            "order_status": o["order_status"],
            "created_at": created.strftime("%d %b %Y, %I:%M %p")
        })

    return render_template("admin/orders.html", orders=formatted_orders)


# =========================
# ORDER DETAIL
# =========================
@admin_bp.route("/order/<int:order_id>")
def order_detail(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT
            orders.*,
            users.name,
            users.email
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE orders.id = ?
        """,
        (order_id,)
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
        "admin/order_detail.html",
        order=order,
        items=items
    )


# =========================
# UPDATE ORDER STATUS
# =========================
@admin_bp.route("/update-order-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    new_status = request.form.get("order_status")

    conn = get_db_connection()

    # Get current status
    order = conn.execute(
        "SELECT order_status FROM orders WHERE id = ?",
        (order_id,)
    ).fetchone()

    if not order:
        conn.close()
        return redirect(url_for("admin.view_orders"))

    old_status = order["order_status"]

    # Only update if changed
    if new_status and new_status != old_status:

        # Update main orders table
        conn.execute(
            "UPDATE orders SET order_status = ? WHERE id = ?",
            (new_status, order_id)
        )

        # Insert into history table
        conn.execute(
            """
            INSERT INTO order_status_history
            (order_id, status, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                order_id,
                new_status,
                f"Order moved to {new_status}",
                int(datetime.now().timestamp())
            )
        )

        conn.commit()

    conn.close()

    return redirect(url_for("admin.view_orders"))



# =========================
# MARK UPI AS PAID
# =========================
@admin_bp.route("/mark-paid/<int:order_id>", methods=["POST"])
def mark_order_paid(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE orders
        SET payment_status = 'PAID'
        WHERE id = ?
        """,
        (order_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("admin.view_orders"))
