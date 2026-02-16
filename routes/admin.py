"""
Admin Blueprint
---------------
Handles:
- Add products
- List products
- Edit products
- Delete products
- View all orders
- Admin dashboard

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
# LIST ALL PRODUCTS
# =========================
@admin_bp.route("/products")
def list_products():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    products = conn.execute(
        """
        SELECT id, name, price, stock, is_new, category
        FROM products
        ORDER BY id DESC
        """
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
            SET name = ?,
                price = ?,
                stock = ?,
                description = ?,
                image = ?,
                is_new = ?,
                category = ?
            WHERE id = ?
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
# ADMIN DASHBOARD
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
    # CANCELLATION RATE
    # -------------------------
    cancelled_orders = conn.execute(
        "SELECT COUNT(*) as c FROM orders WHERE order_status='CANCELLED'"
    ).fetchone()["c"]

    cancellation_rate = 0
    if total_orders > 0:
        cancellation_rate = round((cancelled_orders / total_orders) * 100, 2)

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
    in_transit_orders = 0  # optional placeholder
    cancelled_orders = count_status("CANCELLED")

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
    seven_days_ago = int((datetime.now().timestamp()) - (7 * 86400))

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
    conn.close()

    return redirect(url_for("admin.list_coupons"))


# =========================
# TOGGLE COUPON ACTIVE
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
            "UPDATE coupons SET is_active = ? WHERE id = ?",
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
