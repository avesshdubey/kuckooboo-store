from flask import Blueprint, render_template, session, redirect, url_for
from database.db import get_db_connection

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


# =========================
# ADD TO CART
# =========================
@cart_bp.route("/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    conn = get_db_connection()

    product = conn.execute(
        "SELECT id, name, price, stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    conn.close()

    if not product:
        return "Product not found", 404

    cart = session.get("cart", {})
    pid = str(product_id)

    current_qty = cart.get(pid, {}).get("quantity", 0)

    if current_qty + 1 > product["stock"]:
        session["cart_error"] = "Not enough stock available"
        return redirect(url_for("shop.home"))

    if pid in cart:
        cart[pid]["quantity"] += 1
    else:
        cart[pid] = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": 1
        }

    session["cart"] = cart
    return redirect(url_for("cart.view_cart"))


# =========================
# VIEW CART
# =========================
@cart_bp.route("/")
def view_cart():
    cart = session.get("cart", {})
    total = sum(
        item["price"] * item["quantity"]
        for item in cart.values()
    )

    return render_template(
        "cart/view_cart.html",
        cart=cart,
        total=total
    )


# =========================
# INCREASE QUANTITY
# =========================
@cart_bp.route("/increase/<int:product_id>")
def increase_quantity(product_id):

    cart = session.get("cart", {})
    pid = str(product_id)

    if pid not in cart:
        return redirect(url_for("cart.view_cart"))

    conn = get_db_connection()

    product = conn.execute(
        "SELECT stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    conn.close()

    if not product:
        return redirect(url_for("cart.view_cart"))

    stock = product["stock"]

    if cart[pid]["quantity"] + 1 > stock:
        session["cart_error"] = "Stock limit reached"
        return redirect(url_for("cart.view_cart"))

    cart[pid]["quantity"] += 1
    session["cart"] = cart

    return redirect(url_for("cart.view_cart"))


# =========================
# DECREASE QUANTITY
# =========================
@cart_bp.route("/decrease/<int:product_id>")
def decrease_quantity(product_id):

    cart = session.get("cart", {})
    pid = str(product_id)

    if pid in cart:
        cart[pid]["quantity"] -= 1

        if cart[pid]["quantity"] <= 0:
            cart.pop(pid)

    session["cart"] = cart
    return redirect(url_for("cart.view_cart"))


# =========================
# REMOVE ITEM
# =========================
@cart_bp.route("/remove/<int:product_id>")
def remove_from_cart(product_id):

    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart

    return redirect(url_for("cart.view_cart"))
