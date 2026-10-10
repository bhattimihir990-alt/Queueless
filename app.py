from datetime import timedelta

from flask import Flask, render_template
from flask_cors import CORS

from config import config_by_name
from routes.auth_routes import auth_bp
from routes.citizen_routes import citizen_bp
from routes.staff_routes import staff_bp
from routes.admin_routes import admin_bp
from routes.queue_routes import queue_bp
from routes.api_routes import api_bp


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    app.config.setdefault("SESSION_COOKIE_HTTPONLY", True)
    app.config.setdefault("SESSION_COOKIE_SAMESITE", "Lax")
    app.config.setdefault("PERMANENT_SESSION_LIFETIME", timedelta(hours=8))

    CORS(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(citizen_bp, url_prefix="/citizen")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(queue_bp, url_prefix="/queue")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Direct endpoint aliases for url_for compatibility
    from routes.admin_routes import register_admin
    app.add_url_rule(
        "/admin/register",
        endpoint="register_admin",
        view_func=register_admin,
        methods=["GET", "POST"],
    )

    from routes.auth_routes import admin_login
    app.add_url_rule(
        "/admin/login",
        endpoint="admin_login",
        view_func=admin_login,
        methods=["GET", "POST"],
    )

    @app.template_filter("hhmm")
    def format_hhmm(value):
        if value is None:
            return ""
        if isinstance(value, timedelta):
            total = int(value.total_seconds())
            hours, remainder = divmod(total, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}"
        text = str(value)
        return text[:5] if len(text) >= 5 else text

    @app.route("/")
    def home():
        return render_template("index.html")

    # Global custom HTTP error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/500.html", error=error), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
