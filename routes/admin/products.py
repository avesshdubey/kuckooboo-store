import os
import time
from flask import render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from database.db import get_db_connection
from . import admin_bp


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
# LIST PRODUCTS
# =========================
@admin_bp.route("/products")
def list_products():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()

    products = conn.execute(
        """
        SELECT id, name, price, stock, is_new, category, image
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
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        description = request.form["description"]
        is_new = 1 if request.form.get("is_new") else 0
        category = request.form.get("category", "General")
        created_at = int(time.time())

        image_file = request.files.get("image")
        image_name = None

        if image_file and image_file.filename:
            safe_name = secure_filename(image_file.filename)
            image_name = f"{int(time.time())}_{safe_name}"
            image_file.save(os.path.join(UPLOAD_FOLDER, image_name))

        conn.execute(
            """
            INSERT INTO products
            (name, price, stock, description, image, is_new, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (name, price, stock, description,
             image_name, is_new, category, created_at)
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
        price = float(request.form["price"])
        stock = int(request.form["stock"])
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
