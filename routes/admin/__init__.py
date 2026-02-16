from flask import Blueprint

# Main Admin Blueprint
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Import submodules so routes register
from . import dashboard
from . import products
from . import orders
from . import coupons
