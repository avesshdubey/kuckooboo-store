from flask import Blueprint, render_template, request, redirect, url_for, session
from psycopg2.extras import RealDictCursor
from database.db import get_db_connection
from config import Config
import os
import uuid

shop_bp = Blueprint("shop", __name__)

UPLOAD_FOLDER = "static/review_uploads"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "webm"}


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


# ✅ Proper Cursor Handling (Postgres + SQLite Safe)
def get_cursor(conn):
    if Config.DB_TYPE == "postgres":
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()


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
    cur = get_cursor(conn)

    query = "SELECT * FROM products WHERE 1=1"
    count_query = "SELECT COUNT(*) as count FROM products WHERE 1=1"
    params = []

    placeholder = "%s" if Config.DB_TYPE == "postgres" else "?"

    if search_query:
        query += f" AND name LIKE {placeholder}"
        count_query += f" AND name LIKE {placeholder}"
        params.append(f"%{search_query}%")

    if category:
        query += f" AND category = {placeholder}"
        count_query += f" AND category = {placeholder}"
        params.append(category)

    if sort == "price_low":
        order_by = " ORDER BY price ASC"
    elif sort == "price_high":
        order_by = " ORDER BY price DESC"
    else:
        order_by = " ORDER BY id DESC"

    cur.execute(count_query, params)
    count_result = cur.fetchone()

    if isinstance(count_result, dict):
        total_products = count_result["count"]
    else:
        total_products = count_result[0]

    query += order_by + f" LIMIT {placeholder} OFFSET {placeholder}"
    cur.execute(query, params + [per_page, offset])
    products = cur.fetchall()

    cur.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
    categories = cur.fetchall()

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
        total_pages=total_pages
    )


# =========================
# PRODUCT DETAIL
# =========================
@shop_bp.route("/product/<int:product_id>")
def product_detail(product_id):

    conn = get_db_connection()
    cur = get_cursor(conn)

    placeholder = "%s" if Config.DB_TYPE == "postgres" else "?"

    cur.execute(
        f"SELECT * FROM products WHERE id = {placeholder}",
        (product_id,)
    )
    product = cur.fetchone()

    if not product:
        conn.close()
        return "Product not found", 404

    cur.execute(
        f"""
        SELECT r.*, u.name as user_name
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE r.product_id = {placeholder}
        ORDER BY r.id DESC
        """,
        (product_id,)
    )
    reviews = cur.fetchall()

    cur.execute(
        f"""
        SELECT AVG(rating) as avg_rating,
               COUNT(*) as total
        FROM reviews
        WHERE product_id = {placeholder}
        """,
        (product_id,)
    )
    avg_rating_data = cur.fetchone()

    can_review = False

    if session.get("user_id"):
        cur.execute(
            f"""
            SELECT oi.id
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = {placeholder}
            AND o.user_id = {placeholder}
            AND o.order_status = 'DELIVERED'
            """,
            (product_id, session["user_id"])
        )
        delivered = cur.fetchone()
        if delivered:
            can_review = True

    conn.close()

    avg_rating = 0
    total_reviews = 0

    if avg_rating_data:
        if isinstance(avg_rating_data, dict):
            avg_rating = round(avg_rating_data["avg_rating"], 1) if avg_rating_data["avg_rating"] else 0
            total_reviews = avg_rating_data["total"]
        else:
            avg_rating = round(avg_rating_data[0], 1) if avg_rating_data[0] else 0
            total_reviews = avg_rating_data[1]

    return render_template(
        "shop/product_detail.html",
        product=product,
        reviews=reviews,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
        can_review=can_review
    )


# =========================
# ADD REVIEW
# =========================
@shop_bp.route("/product/<int:product_id>/add-review", methods=["POST"])
def add_review(product_id):

    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    conn = get_db_connection()
    cur = get_cursor(conn)

    placeholder = "%s" if Config.DB_TYPE == "postgres" else "?"

    cur.execute(
        f"""
        SELECT oi.id
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE oi.product_id = {placeholder}
        AND o.user_id = {placeholder}
        AND o.order_status = 'DELIVERED'
        """,
        (product_id, user_id)
    )

    delivered_order = cur.fetchone()

    if not delivered_order:
        conn.close()
        return "You can review only delivered products.", 403

    rating = request.form.get("rating")
    review_text = request.form.get("review_text", "").strip()
    file = request.files.get("media")

    media_filename = None
    media_type = None

    if file and file.filename:
        ext = file.filename.rsplit(".", 1)[1].lower()

        if allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            media_type = "image"
        elif allowed_file(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            media_type = "video"
        else:
            conn.close()
            return "Invalid file type", 400

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(UPLOAD_FOLDER, unique_name))
        media_filename = unique_name

    cur.execute(
        f"""
        SELECT id FROM reviews
        WHERE product_id = {placeholder}
        AND user_id = {placeholder}
        """,
        (product_id, user_id)
    )

    existing_review = cur.fetchone()

    if existing_review:
        cur.execute(
            f"""
            UPDATE reviews
            SET rating = {placeholder},
                review_text = {placeholder},
                media_file = {placeholder},
                media_type = {placeholder}
            WHERE product_id = {placeholder}
            AND user_id = {placeholder}
            """,
            (rating, review_text, media_filename, media_type, product_id, user_id)
        )
    else:
        cur.execute(
            f"""
            INSERT INTO reviews
            (product_id, user_id, rating, review_text, media_file, media_type)
            VALUES ({placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, {placeholder})
            """,
            (product_id, user_id, rating, review_text, media_filename, media_type)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("shop.product_detail", product_id=product_id))


# =========================
# SEARCH
# =========================
@shop_bp.route("/search")
def search():

    query_text = request.args.get("q", "").strip()
    products = []

    if query_text:
        conn = get_db_connection()
        cur = get_cursor(conn)

        placeholder = "%s" if Config.DB_TYPE == "postgres" else "?"

        cur.execute(
            f"""
            SELECT id, name, price, description,
                   stock, image, is_new, category
            FROM products
            WHERE name LIKE {placeholder}
            ORDER BY id DESC
            """,
            (f"%{query_text}%",)
        )
        products = cur.fetchall()
        conn.close()

    return render_template(
        "shop/search.html",
        products=products,
        query=query_text
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

