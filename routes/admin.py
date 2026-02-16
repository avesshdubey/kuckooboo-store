"""
Admin Blueprint
---------------
Handles:
- Dashboard
- List products
- Add products
- Edit products
- Delete products
- View all orders
- Coupons management

Access:
- Admin only (is_admin = 1)
"""

import os
import time
from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db import get_db_connection
from datetime import datetime
from werkzeug.utils import secure_filename

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


# =========================
# LIST PRODUCTS
# =========================
@admin_bp.route("/products")
def list_products():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin/products.html", products=products)


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
        return redirect(url_for("admin.list_products"))

    conn.close()
    return render_template("admin/add_product.html")


# =========================
# EDIT PRODUCT
# =========================
@admin_bp.route("/edit/<int:product_id>", methods=["GET", "POST"])
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
            SET name=?, price=?, stock=?, description=?,
                image=?, is_new=?, category=?
            WHERE id=?
            """,
            (name, price, stock, description,
             image_name, is_new, category, product_id)
        )

        conn.commit()
        conn.close()
        return redirect(url_for("admin.list_products"))

    conn.close()
    return render_template("admin/edit_product.html", product=product)


# =========================
# DELETE PRODUCT
# =========================
@admin_bp.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin.list_products"))


# =========================
# VIEW ORDERS
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

    return render_template("admin/orders.html", orders=orders)


# =========================
# LIST COUPONS
# =========================
@admin_bp.route("/coupons")
def list_coupons():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    coupons = conn.execute(
        "SELECT * FROM coupons ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("admin/coupons.html", coupons=coupons)


# =========================
# ADD COUPON
# =========================
@admin_bp.route("/add-coupon", methods=["POST"])
def add_coupon():
    if not admin_required():
        return redirect(url_for("auth.login"))

    code = request.form["code"].upper().strip()
    discount_type = request.form["discount_type"]
    discount_value = request.form["discount_value"]
    min_order_amount = request.form.get("min_order_amount", 0)
    usage_limit = request.form.get("usage_limit", 0)
    expiry_date = request.form.get("expiry_date")

    created_at = int(datetime.now().timestamp())

    if expiry_date:
        expiry_date = int(datetime.strptime(expiry_date, "%Y-%m-%d").timestamp())
    else:
        expiry_date = None

    conn = get_db_connection()

    try:
        conn.execute(
            """
            INSERT INTO coupons
            (code, discount_type, discount_value, min_order_amount,
             usage_limit, used_count, expiry_date, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, 1, ?)
            """,
            (code, discount_type, discount_value,
             min_order_amount, usage_limit,
             expiry_date, created_at)
        )
        conn.commit()
    except Exception:
        pass

    conn.close()

    return redirect(url_for("admin.list_coupons"))


# =========================
# TOGGLE COUPON
# =========================
@admin_bp.route("/toggle-coupon/<int:coupon_id>", methods=["POST"])
def toggle_coupon(coupon_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    coupon = conn.execute(
        "SELECT is_active FROM coupons WHERE id = ?",
        (coupon_id,)
    ).fetchone()

    if coupon:
        new_status = 0 if coupon["is_active"] else 1
        conn.execute(
            "UPDATE coupons SET is_active=? WHERE id=?",
            (new_status, coupon_id)
        )
        conn.commit()

    conn.close()

    return redirect(url_for("admin.list_coupons"))


# =========================
# DELETE COUPON
# =========================
@admin_bp.route("/delete-coupon/<int:coupon_id>", methods=["POST"])
def delete_coupon(coupon_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM coupons WHERE id = ?",
        (coupon_id,)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("admin.list_coupons"))
