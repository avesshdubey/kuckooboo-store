from flask import session, redirect, url_for

def admin_required():
    """
    Simple admin guard.
    Usage:
        check = admin_required()
        if check:
            return check
    """
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    if not session.get("is_admin"):
        return redirect(url_for("shop.home"))

    return None
