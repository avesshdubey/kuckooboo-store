# =========================
# ORDER PLACED
# =========================
def order_confirmation_email(name, order_id, total):
    subject = "Order Placed - Kuckoo Boo & mama!"

    body = f"""
    <html>
    <body style="background:#f8f8f8;padding:20px;font-family:Arial;">
        <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:10px;">
            <h2 style="color:#e89ab0;">Thank You, {name} 💛</h2>
            <p>Your order has been successfully placed.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total:</strong> ₹{total}</p>
            <hr>
            <p style="font-size:14px;color:#777;">
                We will notify you once it ships.
            </p>
        </div>
    </body>
    </html>
    """

    return subject, body


# =========================
# ORDER CONFIRMED (ADMIN)
# =========================
def order_confirmed_email(name, order_id):
    subject = "Your Order is Confirmed - Kuckoo Boo & mama!"

    body = f"""
Hi {name},

Good news!

Your order (ID: {order_id}) has been confirmed and is being prepared.

We will notify you once it ships.

Thank you for shopping with us!

Team Kuckoo Boo & mama!
"""
    return subject, body


# =========================
# ORDER SHIPPED
# =========================
def order_shipped_email(name, order_id):
    subject = "Your Order Has Been Shipped!"

    body = f"""
Hi {name},

Great news!

Your order (ID: {order_id}) has been shipped.

It will reach you soon.

Thank you for shopping with us!

Team Kuckoo Boo & mama!
"""
    return subject, body


# =========================
# ORDER DELIVERED
# =========================
def order_delivered_email(name, order_id):
    subject = "Order Delivered - Thank You!"

    body = f"""
Hi {name},

Your order (ID: {order_id}) has been delivered.

We hope you love your purchase!

If you enjoyed the product, we would really appreciate your review.

Thank you for choosing Kuckoo Boo & mama!

Team Kuckoo Boo & mama!
"""
    return subject, body


# =========================
# RAZORPAY / UPI PAYMENT CONFIRMED
# =========================
def upi_payment_confirmed_email(name, order_id, total):
    subject = "Payment Confirmed - Kuckoo Boo & mama!"

    body = f"""
    <html>
    <body style="background:#f8f8f8;padding:20px;font-family:Arial;">
        <div style="max-width:600px;margin:auto;background:white;padding:20px;border-radius:10px;">
            <h2 style="color:#28a745;">Payment Received 💚</h2>
            <p>Hi {name},</p>
            <p>We have successfully received your payment.</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Total Paid:</strong> ₹{total}</p>
            <hr>
            <p style="font-size:14px;color:#777;">
                Your order is now being processed.
            </p>
        </div>
    </body>
    </html>
    """

    return subject, body


# =========================
# REVIEW REMINDER
# =========================
def review_reminder_email(name, order_id, review_link):
    subject = "We'd Love Your Feedback - Kuckoo Boo & mama!"

    body = f"""
Hi {name},

Your order (ID: {order_id}) was delivered a few days ago.

We hope you are enjoying it!

Please take a moment to leave your review:

{review_link}

Your feedback helps other customers and supports our small business.

Thank you 💛
Team Kuckoo Boo & mama!
"""
    return subject, body
