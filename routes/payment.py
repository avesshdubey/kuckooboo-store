import json
import logging
import os
from flask import Blueprint, render_template, request, current_app, abort
from database.db import get_db_connection
from config import Config
from payments.razorpay_service import RazorpayService
from utils.email_queue import send_email_async
from utils.email_templates import upi_payment_confirmed_email
import psycopg2.extras


payment_bp = Blueprint("payment", __name__, url_prefix="/payment")


# Helper for DB placeholder + cursor
def get_cursor(conn):
    if Config.DB_TYPE == "postgres":
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()


def ph():
    return "%s" if Config.DB_TYPE == "postgres" else "?"


# =====================================================
# Dedicated Logging Setup
# =====================================================
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "payment_webhook.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

payment_logger = logging.getLogger("payment_logger")

if not payment_logger.handlers:
    payment_logger.setLevel(logging.INFO)
    payment_logger.propagate = False

    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    payment_logger.addHandler(file_handler)

payment_logger.info("Payment logger initialized.")


# =====================================================
# 1️⃣ Create Razorpay Order + Render Checkout
# =====================================================
@payment_bp.route("/razorpay/<int:order_id>")
def razorpay_checkout(order_id):

    conn = get_db_connection()
    cur = get_cursor(conn)

    cur.execute(
        f"SELECT * FROM orders WHERE id = {ph()}",
        (order_id,)
    )
    order = cur.fetchone()
    conn.close()

    if not order:
        abort(404)

    if order["payment_status"] == "PAID":
        return "Payment already completed."

    razorpay_order = RazorpayService.create_order(
        order_id=order["id"],
        amount=order["total_amount"]
    )

    conn = get_db_connection()
    cur = get_cursor(conn)

    cur.execute(
        f"UPDATE orders SET razorpay_order_id = {ph()} WHERE id = {ph()}",
        (razorpay_order["id"], order_id)
    )
    conn.commit()
    conn.close()

    return render_template(
        "checkout/razorpay_checkout.html",
        order=order,
        razorpay_key=current_app.config["RAZORPAY_KEY_ID"],
        razorpay_order_id=razorpay_order["id"]
    )


# =====================================================
# 2️⃣ Webhook
# =====================================================
@payment_bp.route("/webhook", methods=["POST"])
def razorpay_webhook():

    request_body = request.data
    received_signature = request.headers.get("X-Razorpay-Signature")

    if not received_signature:
        payment_logger.warning("Webhook received without signature.")
        abort(400)

    if not RazorpayService.verify_webhook_signature(
        request_body,
        received_signature
    ):
        payment_logger.error("Invalid webhook signature.")
        abort(400)

    payload = RazorpayService.parse_webhook(request_body)
    event = payload.get("event")

    if event != "payment.captured":
        payment_logger.info(f"Ignored event: {event}")
        return {"status": "ignored"}

    payment_entity = payload["payload"]["payment"]["entity"]

    if payment_entity.get("status") != "captured":
        return {"status": "ignored"}

    if payment_entity.get("currency") != "INR":
        abort(400)

    razorpay_order_id = payment_entity["order_id"]
    amount_paid = payment_entity["amount"] / 100

    conn = get_db_connection()
    cur = get_cursor(conn)

    cur.execute(
        f"SELECT * FROM orders WHERE razorpay_order_id = {ph()}",
        (razorpay_order_id,)
    )
    order = cur.fetchone()

    if not order:
        conn.close()
        abort(404)

    if order["payment_status"] == "PAID":
        conn.close()
        return {"status": "already_processed"}

    if float(order["total_amount"]) != float(amount_paid):
        conn.close()
        abort(400)

    # Update status
    cur.execute(
        f"""
        UPDATE orders
        SET payment_status = 'PAID',
            order_status = 'CONFIRMED'
        WHERE id = {ph()}
        """,
        (order["id"],)
    )

    conn.commit()
    conn.close()

    payment_logger.info(
        f"Payment marked PAID and order CONFIRMED for order {order['id']}"
    )

    # Send email
    if order.get("email"):
        subject, html_content = upi_payment_confirmed_email(
            order["full_name"],
            order["id"],
            order["total_amount"]
        )

        send_email_async(
            order["email"],
            subject,
            html_content,
            is_html=True
        )

    return {"status": "success"}


# =====================================================
# 3️⃣ Payment Failure Page
# =====================================================
@payment_bp.route("/failure/<int:order_id>")
def payment_failure(order_id):

    conn = get_db_connection()
    cur = get_cursor(conn)

    cur.execute(
        f"SELECT * FROM orders WHERE id = {ph()}",
        (order_id,)
    )
    order = cur.fetchone()
    conn.close()

    if not order:
        abort(404)

    return render_template(
        "checkout/payment_failed.html",
        order=order
    )
