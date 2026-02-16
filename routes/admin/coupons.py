from flask import render_template, request, redirect, url_for, session
from database.db import get_db_connection
from datetime import datetime
from . import admin_bp


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
