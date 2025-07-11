from kittie_app.env import load_env_vars
load_env_vars()

from flask import Flask, request, render_template
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

from datetime import datetime


db = SQLAlchemy()
DB_NAME = "project_details.db"

mail = Mail()


def create_app():
    app = Flask(__name__)
    app.config.from_object("kittie_app.config.DevConfig")

    db.init_app(app)
    Migrate(app, db)
    mail.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        from kittie_app.models import User
        return User.query.get(int(id))
    
    from kittie_app.views import views
    from kittie_app.auth import auth
    from kittie_app.cookies import cooks
    for bp in (views, auth, cooks):
        app.register_blueprint(bp)

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

    @app.errorhandler(404)
    def page_not_found(error):
        kittie_production = None
        return render_template('error_404.html', user=current_user, kittie_production=kittie_production), 404
    

    return app