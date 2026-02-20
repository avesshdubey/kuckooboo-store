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

    # ✅ FIXED COUNT QUERY
    count_query = "SELECT COUNT(*) as count " + base_query
    count_row = conn.execute(count_query, params).fetchone()
    total_products = count_row["count"]

    # ✅ PREVIEW IMAGE SUBQUERY
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
# ADD REVIEW
# =========================
@shop_bp.route("/product/<int:product_id>/add-review", methods=["POST"])
def add_review(product_id):

    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    conn = get_db_connection()

    delivered_order = conn.execute(
        """
        SELECT oi.id
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE oi.product_id = %s
        AND o.user_id = %s
        AND o.order_status = 'DELIVERED'
        """,
        (product_id, user_id)
    ).fetchone()

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

    existing_review = conn.execute(
        """
        SELECT id FROM reviews
        WHERE product_id = %s
        AND user_id = %s
        """,
        (product_id, user_id)
    ).fetchone()

    if existing_review:
        conn.execute(
            """
            UPDATE reviews
            SET rating = %s,
                review_text = %s,
                media_file = %s,
                media_type = %s
            WHERE product_id = %s
            AND user_id = %s
            """,
            (rating, review_text, media_filename, media_type, product_id, user_id)
        )
    else:
        conn.execute(
            """
            INSERT INTO reviews
            (product_id, user_id, rating, review_text, media_file, media_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (product_id, user_id, rating, review_text, media_filename, media_type)
        )

    conn.commit()
    conn.close()

    return redirect(url_for("shop.product_detail", product_id=product_id))


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
    from database.db import get_db_connection

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