import time
from flask import render_template, request, redirect, url_for, session
from database.db import get_db_connection
from . import admin_bp

import cloudinary
import cloudinary.uploader
import os


# =========================
# CLOUDINARY CONFIG
# =========================
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


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

        # Insert product first
        cursor = conn.execute(
            """
            INSERT INTO products
            (name, price, stock, description, is_new, category, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (name, price, stock, description,
             is_new, category, created_at)
        )

        product_id = cursor.fetchone()["id"]

        # Handle Multiple Images
        images = request.files.getlist("images")

        for image in images:
            if image and image.filename:
                upload_result = cloudinary.uploader.upload(image)
                conn.execute(
                    """
                    INSERT INTO product_media
                    (product_id, media_url, media_type, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        product_id,
                        upload_result["secure_url"],
                        "image",
                        int(time.time())
                    )
                )

        # Handle Optional Video
        video = request.files.get("video")

        if video and video.filename:
            upload_result = cloudinary.uploader.upload(
                video,
                resource_type="video"
            )

            conn.execute(
                """
                INSERT INTO product_media
                (product_id, media_url, media_type, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    product_id,
                    upload_result["secure_url"],
                    "video",
                    int(time.time())
                )
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
        image_url = product["image"]

        # If new image uploaded → replace in Cloudinary
        if image_file and image_file.filename:
            upload_result = cloudinary.uploader.upload(image_file)
            image_url = upload_result["secure_url"]

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
             image_url, is_new, category, product_id)
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
