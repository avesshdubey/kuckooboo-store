import razorpay
import hmac
import hashlib
import json
from flask import current_app


class RazorpayService:
    """
    Handles all direct communication with Razorpay API.
    No business logic. No DB logic. Only gateway logic.
    """

    @staticmethod
    def get_client():
        """
        Initialize Razorpay client using config keys.
        """
        return razorpay.Client(
            auth=(
                current_app.config["RAZORPAY_KEY_ID"],
                current_app.config["RAZORPAY_KEY_SECRET"]
            )
        )

    @staticmethod
    def create_order(order_id: int, amount: float):
        """
        Creates Razorpay order.
        Razorpay expects amount in paise.
        """

        client = RazorpayService.get_client()

        razorpay_order = client.order.create({
            "amount": int(amount * 100),  # Convert INR to paise
            "currency": "INR",
            "receipt": f"order_{order_id}",
            "payment_capture": 1
        })

        return razorpay_order

    @staticmethod
    def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify frontend payment signature (optional extra layer).
        """

        body = f"{razorpay_order_id}|{razorpay_payment_id}"

        expected_signature = hmac.new(
            current_app.config["RAZORPAY_KEY_SECRET"].encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, razorpay_signature)

    @staticmethod
    def verify_webhook_signature(request_body, received_signature):
        """
        Verify Razorpay webhook signature.
        This is CRITICAL for security.
        """

        webhook_secret = current_app.config["RAZORPAY_WEBHOOK_SECRET"]

        expected_signature = hmac.new(
            webhook_secret.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, received_signature)

    @staticmethod
    def parse_webhook(request_body):
        """
        Safely parse webhook JSON payload.
        """
        return json.loads(request_body.decode("utf-8"))
