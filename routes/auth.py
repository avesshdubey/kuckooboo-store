from flask import Blueprint, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db_connection
from utils.email import send_reset_email
import secrets
import time

auth_bp = Blueprint("auth", __name__)


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            return "All fields are required"

        password_hash = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash)
            )
            conn.commit()

        except Exception:
            conn.rollback()
            conn.close()
            return "Email already registered"

        conn.close()
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            return "Email and password are required"

        conn = get_db_connection()

        user = conn.execute(
            """
            SELECT id, name, password_hash, is_admin
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["is_admin"] = bool(user["is_admin"])
            return redirect(url_for("shop.home"))

        return "Invalid email or password"

    return render_template("auth/login.html")


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("shop.home"))


# =========================
# FORGOT PASSWORD
# =========================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    message = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            return "Email is required"

        token = secrets.token_urlsafe(32)
        expiry = int(time.time()) + 3600  # 1 hour

        conn = get_db_connection()

        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            conn.execute(
                """
                UPDATE users
                SET reset_token = ?,
                    reset_token_expiry = ?
                WHERE email = ?
                """,
                (token, expiry, email)
            )
            conn.commit()

            reset_link = request.host_url.rstrip("/") + url_for(
                "auth.reset_password",
                token=token
            )

            send_reset_email(email, reset_link)

        conn.close()

        message = "If the email exists, a reset link has been sent."

    return render_template(
        "auth/forgot_password.html",
        message=message
    )


# =========================
# RESET PASSWORD
# =========================
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    conn = get_db_connection()

    user = conn.execute(
        """
        SELECT id, reset_token_expiry
        FROM users
        WHERE reset_token = ?
        """,
        (token,)
    ).fetchone()

    if not user or user["reset_token_expiry"] < int(time.time()):
        conn.close()
        return "Invalid or expired token"

    if request.method == "POST":
        password = request.form.get("password", "").strip()

        if not password:
            conn.close()
            return "Password cannot be empty"

        password_hash = generate_password_hash(password)

        conn.execute(
            """
            UPDATE users
            SET password_hash = ?,
                reset_token = NULL,
                reset_token_expiry = NULL
            WHERE reset_token = ?
            """,
            (password_hash, token)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("auth.login"))

    conn.close()
    return render_template("auth/reset_password.html")
