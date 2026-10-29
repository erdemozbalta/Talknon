from flask import Blueprint

business_bp = Blueprint('business', __name__, url_prefix='/business')

from app.blueprints.business import routes
