from flask import Blueprint

user_bp = Blueprint('user', __name__, url_prefix='/profile')

from app.blueprints.user import routes
