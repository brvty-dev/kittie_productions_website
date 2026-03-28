from kittie_app.env import load_env_vars
load_env_vars()

from flask import Flask, request, render_template
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from datetime import datetime
import os


db = SQLAlchemy()
mail = Mail()
migrate = Migrate()

DB_NAME = "project_details.db"


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object("kittie_app.config.DevConfig")

    os.makedirs(app.instance_path, exist_ok=True)

    project_files_folder = os.path.join(
        app.instance_path,
        app.config["PROJECT_FILES_UPLOAD_FOLDER"]
    )

    os.makedirs(project_files_folder, exist_ok=True)

    app.config["PROJECT_FILES_UPLOAD_FOLDER_ABS"] = project_files_folder

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        from kittie_app.models import User
        return User.query.get(int(id))
    
    from kittie_app.views import views, corp
    from kittie_app.auth import auth
    from kittie_app.cookies import cooks
    from kittie_app.production_routes import prod
    from kittie_app.user_routes import users
    
    for bp in (views, auth, cooks, prod, users):
        app.register_blueprint(bp)
    app.register_blueprint(corp, url_prefix="/corporate_pages/")

    from kittie_app.utils import generate_csrf_token
    app.jinja_env.globals.update({
        'csrf_token': generate_csrf_token,
    })

    @app.context_processor
    def inject_globals():
        return {
            'cookie_accepted': request.cookies.get('cookie_accepted'),
            'cookie_rejected': request.cookies.get('cookie_rejected'),
            'message_viewed_closed': request.cookies.get('message_viewed_closed'),
            'current_year': datetime.now().year,
        }

    @app.errorhandler(403)
    def forbidden(error):
        kittie_production = None
        return render_template('error_403.html', user=current_user, kittie_production=kittie_production), 403

    @app.errorhandler(404)
    def page_not_found(error):
        kittie_production = None
        return render_template('error_404.html', user=current_user, kittie_production=kittie_production), 404
    

    return app