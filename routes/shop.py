from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db import get_db_connection
import os
import uuid

shop_bp = Blueprint("shop", __name__)

UPLOAD_FOLDER = "static/review_uploads"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "webm"}


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


# =========================
# HOME / PRODUCT LIST
# =========================
@shop_bp.route("/")
def home():
    search_query = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "").strip()
    page = request.args.get("page", 1, type=int)

    per_page = 8
    offset = (page - 1) * per_page

    conn = get_db_connection()

    base_query = " FROM products p WHERE 1=1 "
    params = []

    if search_query:
        base_query += " AND p.name ILIKE %s "
        params.append(f"%{search_query}%")

    if category:
        base_query += " AND p.category = %s "
        params.append(category)

    if sort == "price_low":
        order_by = " ORDER BY p.price ASC "
    elif sort == "price_high":
        order_by = " ORDER BY p.price DESC "
    else:
        order_by = " ORDER BY p.id DESC "

    count_query = "SELECT COUNT(*) as count " + base_query
    count_row = conn.execute(count_query, params).fetchone()
    total_products = count_row["count"]

    query = """
        SELECT p.*,
        (
            SELECT pm.media_url
            FROM product_media pm
            WHERE pm.product_id = p.id
            ORDER BY pm.id ASC
            LIMIT 1
        ) AS preview_image
    """ + base_query + order_by + " LIMIT %s OFFSET %s "

    products = conn.execute(query, params + [per_page, offset]).fetchall()

    categories = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category ASC"
    ).fetchall()

    # =========================
    # DYNAMIC ACTIVE COUPON
    # =========================
    active_coupon = conn.execute(
        """
        SELECT code, discount_type, discount_value
        FROM coupons
        WHERE is_active = 1
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    conn.close()

    total_pages = (total_products + per_page - 1) // per_page

    return render_template(
        "shop/home.html",
        products=products,
        search_query=search_query,
        categories=categories,
        selected_category=category,
        sort=sort,
        page=page,
        total_pages=total_pages,
        active_coupon=active_coupon   # ✅ passed to template
    )


# =========================
# PRODUCT DETAIL
# =========================
@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):

    conn = get_db_connection()

    product = conn.execute(
        "SELECT * FROM products WHERE id = %s",
        (product_id,)
    ).fetchone()

    if not product:
        conn.close()
        return "Product not found", 404

    media = conn.execute(
        """
        SELECT media_url, media_type
        FROM product_media
        WHERE product_id = %s
        ORDER BY id ASC
        """,
        (product_id,)
    ).fetchall()

    reviews = conn.execute(
        """
        SELECT r.*, u.name as user_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.product_id = %s
        ORDER BY r.id DESC
        """,
        (product_id,)
    ).fetchall()

    avg_rating_data = conn.execute(
        """
        SELECT AVG(rating) as avg_rating,
               COUNT(*) as total
        FROM reviews
        WHERE product_id = %s
        """,
        (product_id,)
    ).fetchone()

    can_review = False

    if session.get("user_id"):
        delivered = conn.execute(
            """
            SELECT oi.id
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = %s
            AND o.user_id = %s
            AND o.order_status = 'DELIVERED'
            """,
            (product_id, session["user_id"])
        ).fetchone()

        if delivered:
            can_review = True

    conn.close()

    avg_rating = round(avg_rating_data["avg_rating"], 1) if avg_rating_data["avg_rating"] else 0
    total_reviews = avg_rating_data["total"]

    return render_template(
        "shop/product_detail.html",
        product=product,
        media=media,
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        can_review=can_review
    )


# =========================
# STATIC PAGES
# =========================
@shop_bp.route("/about")
def about():
    return render_template("about.html")


@shop_bp.route("/contact")
def contact():
    return render_template("contact.html")


# =========================
# SEARCH
# =========================
@shop_bp.route("/search")
def search():

    query = request.args.get("q", "").strip()

    conn = get_db_connection()

    if query:
        search_term = f"%{query}%"

        products = conn.execute("""
            SELECT p.*,
                   (
                       SELECT pm.media_url
                       FROM product_media pm
                       WHERE pm.product_id = p.id
                       LIMIT 1
                   ) AS preview_image
            FROM products p
            WHERE p.name ILIKE %s
               OR p.description ILIKE %s
            ORDER BY p.created_at DESC
        """, (search_term, search_term)).fetchall()
    else:
        products = []

    conn.close()

    return render_template(
        "shop/search.html",
        products=products,
        query=query
    )