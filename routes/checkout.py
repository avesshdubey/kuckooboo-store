from flask import Blueprint, session, redirect, url_for, render_template, request
from database.db import get_db_connection
from utils.email_templates import order_confirmation_email
from utils.email_queue import send_email_async
import time
import uuid
import urllib.parse

checkout_bp = Blueprint("checkout", __name__, url_prefix="/checkout")


# =========================
# CHECKOUT PAGE
# =========================
@checkout_bp.route("/", methods=["GET"])
def checkout():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    cart = session.get("cart", {})
    if not cart:
        return redirect(url_for("cart.view_cart"))

    # Prevent duplicate submissions
    session["checkout_token"] = str(uuid.uuid4())

    total = sum(item["price"] * item["quantity"] for item in cart.values())

    return render_template(
        "checkout/checkout.html",
        cart=cart,
        total=total,
        checkout_token=session["checkout_token"]
    )


# =========================
# PLACE ORDER
# =========================
@checkout_bp.route("/place-order", methods=["POST"])
def place_order():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    cart = session.get("cart", {})
    payment_method = request.form.get("payment_method")
    token = request.form.get("checkout_token")

    # =========================
    # SECURITY VALIDATION
    # =========================
    if not token or token != session.get("checkout_token"):
        return "Duplicate or invalid order request", 400

    if not cart or payment_method not in ["COD", "RAZORPAY"]:
        return redirect(url_for("checkout.checkout"))

    # =========================
    # SHIPPING DETAILS
    # =========================
    full_name = request.form["full_name"]
    phone = request.form["phone"]
    address = request.form["address"]
    city = request.form["city"]
    state = request.form["state"]
    pincode = request.form["pincode"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # STOCK VALIDATION
    # =========================
    for product_id, item in cart.items():
        product = cursor.execute(
            "SELECT stock FROM products WHERE id = ?",
            (product_id,)
        ).fetchone()

        if not product or product["stock"] < item["quantity"]:
            conn.close()
            return "Insufficient stock", 400

    total = sum(item["price"] * item["quantity"] for item in cart.values())

    # =========================
    # CORRECT PAYMENT STATUS LOGIC
    # =========================
    # COD → Paid (manual confirmation outside system)
    # Razorpay → Pending (will update via webhook)
    payment_status = "PAID" if payment_method == "COD" else "PENDING"

    cursor.execute(
        """
        INSERT INTO orders (
            user_id, total_amount, payment_method, payment_status,
            order_status, full_name, phone, address, city, state, pincode, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            total,
            payment_method,
            payment_status,
            "PLACED",
            full_name,
            phone,
            address,
            city,
            state,
            pincode,
            int(time.time()),
        ),
    )

    order_id = cursor.lastrowid

    # =========================
    # INSERT ORDER ITEMS + UPDATE STOCK
    # =========================
    for product_id, item in cart.items():
        cursor.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                order_id,
                product_id,
                item["name"],
                item["quantity"],
                item["price"],
            ),
        )

        cursor.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (item["quantity"], product_id),
        )

    conn.commit()

    # =========================
    # SEND ORDER CONFIRMATION EMAIL
    # =========================
    user = conn.execute(
        "SELECT email FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()

    if user:
        subject, body = order_confirmation_email(
            full_name,
            order_id,
            total
        )

        send_email_async(
            user["email"],
            subject,
            body,
            is_html=True
        )

    conn.close()

    # =========================
    # CLEAR CART + TOKEN
    # =========================
    session.pop("cart", None)
    session.pop("checkout_token", None)

    # =========================
    # PAYMENT FLOW
    # =========================

    # Razorpay → Redirect to payment page
    if payment_method == "RAZORPAY":
        return redirect(
            url_for("payment.razorpay_checkout", order_id=order_id)
        )

    # COD → WhatsApp confirmation redirect
    whatsapp_number = "918853121180"

    message = f"""
Hello Kuckoo Boo!

I just placed an order.

Order ID: {order_id}
Name: {full_name}
Total: ₹{total}
Payment Method: COD

Please confirm my order.
"""

    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

    return redirect(whatsapp_url)


# =========================
# SUCCESS PAGE
# =========================
@checkout_bp.route("/success")
def success():
    return render_template("checkout/success.html")
