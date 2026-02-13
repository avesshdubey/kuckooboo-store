"""
Admin Blueprint
---------------
Handles:
- Add products
- Edit products (image + new arrival)
- Delete products
- View all orders
- Update order status
- Mark UPI orders as PAID
- Admin dashboard
- Order detail view

Access:
- Admin only (is_admin = 1)
"""

import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db import get_db_connection
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.email_queue import send_email_async

# ✅ EMAIL IMPORTS
from utils.email import send_email
from utils.email_templates import (
    order_confirmed_email,
    order_shipped_email,
    order_delivered_email,
    upi_payment_confirmed_email,
    review_reminder_email
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
# ADD PRODUCT
# =========================
@admin_bp.route("/add-product", methods=["GET", "POST"])
def add_product():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]
        description = request.form["description"]
        is_new = 1 if request.form.get("is_new") else 0
        category = request.form.get("category", "General")

        image_file = request.files.get("image")
        image_name = None

        if image_file and image_file.filename:
            safe_name = secure_filename(image_file.filename)
            image_name = f"{int(time.time())}_{safe_name}"
            image_file.save(os.path.join(UPLOAD_FOLDER, image_name))

        conn.execute(
            """
            INSERT INTO products 
            (name, price, stock, description, image, is_new, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, price, stock, description, image_name, is_new, category)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("admin.add_product"))

    conn.close()
    return render_template("admin/add_product.html")


# =========================
# EDIT PRODUCT
# =========================
@admin_bp.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        return "Product not found", 404

    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        stock = request.form["stock"]
        description = request.form["description"]
        is_new = 1 if request.form.get("is_new") else 0
        category = request.form.get("category", "General")

        image_file = request.files.get("image")
        image_name = product["image"]

        if image_file and image_file.filename:
            safe_name = secure_filename(image_file.filename)
            image_name = f"{int(time.time())}_{safe_name}"
            image_file.save(os.path.join(UPLOAD_FOLDER, image_name))

        conn.execute(
            """
            UPDATE products
            SET name = ?, price = ?, stock = ?, description = ?, 
                image = ?, is_new = ?, category = ?
            WHERE id = ?
            """,
            (name, price, stock, description,
             image_name, is_new, category, product_id)
        )
        conn.commit()
        conn.close()

        return redirect(url_for("shop.home"))

    conn.close()
    return render_template("admin/edit_product.html", product=product)


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

    formatted_orders = [
        {
            "id": o["id"],
            "customer_name": o["customer_name"],
            "customer_email": o["customer_email"],
            "total_amount": o["total_amount"],
            "payment_method": o["payment_method"],
            "payment_status": o["payment_status"],
            "order_status": o["order_status"],
            "created_at": datetime.fromtimestamp(o["created_at"]).strftime(
                "%d %b %Y, %I:%M %p"
            )
        }
        for o in orders
    ]

    return render_template("admin/orders.html", orders=formatted_orders)

# =========================
# UPDATE ORDER STATUS
# =========================
# =========================
# UPDATE ORDER STATUS
# =========================
@admin_bp.route("/update-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    new_status = request.form.get("order_status")

    allowed_statuses = [
        "PLACED", "CONFIRMED",
        "SHIPPED", "DELIVERED", "CANCELLED"
    ]

    if new_status not in allowed_statuses:
        return "Invalid status", 400

    conn = get_db_connection()

    # Fetch user + payment status BEFORE update
    order = conn.execute(
        """
        SELECT users.email,
               users.name,
               orders.payment_status,
               orders.total_amount
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE orders.id = ?
        """,
        (order_id,)
    ).fetchone()

    if not order:
        conn.close()
        return "Order not found", 404

    # Update status
    conn.execute(
        "UPDATE orders SET order_status = ? WHERE id = ?",
        (new_status, order_id)
    )
    conn.commit()

    email = order["email"]
    name = order["name"]
    payment_status = order["payment_status"]
    total = order["total_amount"]

    # -----------------------
    # CONFIRMED
    # -----------------------
    if new_status == "CONFIRMED":
        subject, body = order_confirmed_email(name, order_id)
        send_email_async(email, subject, body, is_html=True)

    # -----------------------
    # SHIPPED
    # -----------------------
    elif new_status == "SHIPPED":
        subject, body = order_shipped_email(name, order_id)
        send_email_async(email, subject, body, is_html=True)

    # -----------------------
    # DELIVERED (WITH INVOICE)
    # -----------------------
    elif new_status == "DELIVERED":

        # Only send invoice if payment is completed
        if payment_status == "PAID":

            items = conn.execute(
                """
                SELECT product_name, quantity, price
                FROM order_items
                WHERE order_id = ?
                """,
                (order_id,)
            ).fetchall()

            from utils.invoice import generate_invoice

            invoice_path = generate_invoice(
                order_id,
                name,
                items,
                total
            )

            subject, body = order_delivered_email(name, order_id)

            send_email_async(
                email,
                subject,
                body,
                is_html=True,
                attachment_path=invoice_path
            )

    conn.close()

    return redirect(url_for("admin.view_orders"))

# =========================
# MARK ORDER AS PAID
# =========================
@admin_bp.route("/mark-paid/<int:order_id>", methods=["POST"])
def mark_order_paid(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT users.email, users.name
        FROM orders
        JOIN users ON orders.user_id = users.id
        WHERE orders.id = ?
        """,
        (order_id,)
    ).fetchone()

    conn.execute(
        "UPDATE orders SET payment_status = 'PAID' WHERE id = ?",
        (order_id,)
    )
    conn.commit()

    if order:
        subject, body = upi_payment_confirmed_email(
            order["name"],
            order_id
        )
        send_email(order["email"], subject, body)

    conn.close()

    return redirect(url_for("admin.view_orders"))


# =========================
# ADMIN DASHBOARD
# =========================
@admin_bp.route("/dashboard")
def dashboard():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    # --------------------------
    # REVIEW REMINDER LOGIC
    # --------------------------
    three_days_ago = int(time.time()) - (3 * 24 * 60 * 60)

    reminders = conn.execute(
        """
        SELECT DISTINCT orders.id, users.name, users.email
        FROM orders
        JOIN users ON orders.user_id = users.id
        JOIN order_items ON order_items.order_id = orders.id
        LEFT JOIN reviews 
            ON reviews.product_id = order_items.product_id
            AND reviews.user_id = orders.user_id
        WHERE orders.order_status = 'DELIVERED'
        AND orders.review_reminder_sent = 0
        AND orders.created_at <= ?
        AND reviews.id IS NULL
        """,
        (three_days_ago,)
    ).fetchall()

    for order in reminders:
        review_link = request.host_url.rstrip("/") + "/my-orders"

        subject, body = review_reminder_email(
            order["name"],
            order["id"],
            review_link
        )

        send_email_async(order["email"], subject, body, is_html=True)

        conn.execute(
            "UPDATE orders SET review_reminder_sent = 1 WHERE id = ?",
            (order["id"],)
        )

    conn.commit()

    # --------------------------
    # ORDER STATS
    # --------------------------
    total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    placed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='PLACED'").fetchone()[0]
    confirmed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='CONFIRMED'").fetchone()[0]
    shipped_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='SHIPPED'").fetchone()[0]
    delivered_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='DELIVERED'").fetchone()[0]
    cancelled_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE order_status='CANCELLED'").fetchone()[0]

    total_revenue = conn.execute(
        """
        SELECT COALESCE(SUM(total_amount),0)
        FROM orders
        WHERE order_status='DELIVERED'
        AND payment_status='PAID'
        """
    ).fetchone()[0]

    # --------------------------
    # DAILY SALES
    # --------------------------
    daily_sales_raw = conn.execute(
        """
        SELECT DATE(datetime(created_at,'unixepoch')) as sale_date,
               SUM(total_amount) as daily_total
        FROM orders
        WHERE order_status='DELIVERED'
        AND payment_status='PAID'
        GROUP BY sale_date
        ORDER BY sale_date ASC
        """
    ).fetchall()

    daily_sales = [
        {
            "sale_date": row["sale_date"],
            "daily_total": row["daily_total"]
        }
        for row in daily_sales_raw
    ]

    # --------------------------
    # TOP PRODUCTS
    # --------------------------
    top_products_raw = conn.execute(
        """
        SELECT product_name, SUM(quantity) as total_sold
        FROM order_items
        GROUP BY product_name
        ORDER BY total_sold DESC
        LIMIT 5
        """
    ).fetchall()

    top_products = [
        {
            "product_name": row["product_name"],
            "total_sold": row["total_sold"]
        }
        for row in top_products_raw
    ]

    # --------------------------
    # INVENTORY
    # --------------------------
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    out_of_stock = conn.execute("SELECT COUNT(*) FROM products WHERE stock=0").fetchone()[0]
    total_stock_units = conn.execute("SELECT COALESCE(SUM(stock),0) FROM products").fetchone()[0]

    low_stock_products = conn.execute(
        """
        SELECT id, name, stock
        FROM products
        WHERE stock <= 5
        ORDER BY stock ASC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_orders=total_orders,
        placed_orders=placed_orders,
        confirmed_orders=confirmed_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_revenue=total_revenue,
        daily_sales=daily_sales,
        top_products=top_products,
        total_products=total_products,
        out_of_stock=out_of_stock,
        total_stock_units=total_stock_units,
        low_stock_products=low_stock_products
    )


# =========================
# DELETE PRODUCT
# =========================
@admin_bp.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    product = conn.execute(
        "SELECT image FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    if product and product["image"]:
        image_path = os.path.join(UPLOAD_FOLDER, product["image"])
        if os.path.exists(image_path):
            os.remove(image_path)

    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("shop.home"))


# =========================
# ORDER DETAIL (ADMIN)
# =========================
@admin_bp.route("/order/<int:order_id>")
def order_detail(order_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    order = conn.execute(
        """
        SELECT
            orders.id,
            orders.total_amount,
            orders.payment_method,
            orders.payment_status,
            orders.order_status,
            orders.created_at,
            users.name AS customer_name,
            users.email AS customer_email,
            orders.full_name,
            orders.phone,
            orders.address,
            orders.city,
            orders.state,
            orders.pincode
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
