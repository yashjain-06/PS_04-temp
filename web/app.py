"""Flask app factory (owner: M4)."""
from flask import Flask, render_template

from web.api.blueprint_routes import bp as blueprint_bp
from web.api.logistics_routes import bp as logistics_bp
from web.api.ml_routes import bp as ml_bp
from web.api.metrics_routes import bp as results_bp
from web.api.sim_routes import bp as sim_bp
from web.services import session_store
from web.api.stream_routes import bp as stream_bp


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    session_store.init_app(app)
    app.register_blueprint(sim_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(logistics_bp)
    app.register_blueprint(blueprint_bp)
    app.register_blueprint(ml_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/editor")
    def editor():
        return render_template("blueprint_editor.html")

    @app.get("/insights")
    def insights_page():
        return render_template("insights.html")

    @app.get("/logistics")
    def logistics():
        return render_template("logistics.html")

    @app.get("/experiments")
    def experiments():
        return render_template("experiments.html")

    @app.get("/about")
    def about():
        return render_template("about.html")

    return app
