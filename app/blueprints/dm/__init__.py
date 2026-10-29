from flask import Blueprint

dm_bp = Blueprint('dm', __name__, url_prefix='/dm')

from app.blueprints.dm import routes
