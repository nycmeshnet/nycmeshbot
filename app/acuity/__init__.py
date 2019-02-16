from flask import Blueprint

bp = Blueprint('acuity', __name__)

from app.acuity import routes
