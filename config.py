
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ==========================
    # Core App Configuration
    # ==========================
    SECRET_KEY = os.environ.get("dev-secret-key-change-later")
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "store.db")

    # ==========================
    # Mail Configuration
    # ==========================
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("avedaaaaaaaa@gmail.com")
    MAIL_PASSWORD = os.environ.get("lowc lede hzhw bjlj")

    # ==========================
    # Razorpay Configuration
    # ==========================
    RAZORPAY_KEY_ID = os.environ.get("rzp_test_SFez0KcP5aZD3s")
    RAZORPAY_KEY_SECRET = os.environ.get("CjZqeX2Q5VOzQBEwxbZJO5Wa")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("kuckoo_webhook_secure_2026")
