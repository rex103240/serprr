from flask import Blueprint

# 1. Define Standard Blueprints (Only for those using the old circular import pattern)
auth = Blueprint('auth', __name__)
members = Blueprint('members', __name__)
plans = Blueprint('plans', __name__)
equipment = Blueprint('equipment', __name__)
reports = Blueprint('reports', __name__)
api = Blueprint('api', __name__)
settings = Blueprint('settings', __name__)

# 2. Import ACTUAL Blueprints (The Fix)
from .finance_routes import finance_bp as finance
from .main_routes import main_bp as main
from .staff_routes import staff_routes as staff

# 3. Import Views for Standard Blueprints
from . import auth_routes, member_routes, plan_routes, equipment_routes, report_routes, api_routes, settings_routes