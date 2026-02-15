import os
from flask import Flask
from config import Config

# Blueprints
from routes.auth import auth_bp
from routes.shop import shop_bp
from routes.cart import cart_bp
from routes.checkout import checkout_bp
from routes.user import user_bp
from routes.admin import admin_bp
from routes.payment import payment_bp  # ✅ NEW


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(payment_bp)  # ✅ NEW

    
    @app.route("/__init_db_once")
    def init_db_once():
        from database.init_db import init_db
        init_db()
        return "Database initialized successfully."
    return app   # ✅ VERY IMPORTANT


# Create app instance
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


   