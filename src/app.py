import os
from datetime import datetime
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from src.config import Config
from src.models import db, User, init_db
from src.utils.helpers import format_date, format_datetime, format_currency

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    
    csrf = CSRFProtect(app)
    os.makedirs(os.path.join(app.static_folder, "uploads"), exist_ok=True)
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["format_currency"] = format_currency
    
    @app.context_processor
    def inject_globals():
        return {
            "gym_name": app.config.get("LICENSE_HOLDER", "IronLifter Gym"),
            "version": "10.1",
            "grace_period": app.config.get("GRACE_PERIOD_DAYS"),
            "now": datetime.now,
        }
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500
    
    from src.routes import main, auth, members, plans, staff, equipment, finance, reports, api, settings
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(members, url_prefix="/members")
    app.register_blueprint(plans, url_prefix="/plans")
    app.register_blueprint(staff, url_prefix="/staff")
    app.register_blueprint(equipment, url_prefix="/equipment")
    app.register_blueprint(finance, url_prefix="/finance")
    app.register_blueprint(reports, url_prefix="/reports")
    app.register_blueprint(api, url_prefix="/api")
    app.register_blueprint(settings, url_prefix="/settings")
    
    init_db(app)
    return app

app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
