import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ==========================
    # Core App Configuration
    # ==========================
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret")
    DATABASE_PATH = os.path.join(BASE_DIR, "database", "store.db")

    # ==========================
    # Mail Configuration
    # ==========================
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # ==========================
    # Razorpay Configuration
    # ==========================
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET")
