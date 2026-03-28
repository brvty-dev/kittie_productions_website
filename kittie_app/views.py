from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort, send_from_directory
from flask_login import login_required, current_user
from kittie_app.models import db, User, kittie_production_database, ProductionAuditLog, Permission, UserAuditLog, PermissionAuditLog, FileAuditLog, FileAccessLog
from kittie_app.utils import generate_secure_token, send_welcome_email, allowed_file, save_uploaded_file
import os


views = Blueprint('views', __name__)
corp = Blueprint('corp', __name__)


@views.route('/')
def index():
    kittie_production = None
    return render_template("index.html", user=current_user, kittie_production=kittie_production)


@views.route('/about')
def about():
    kittie_production = None
    return render_template("about.html", user=current_user, kittie_production=kittie_production)


@views.route('/gallery')
def gallery():
    kittie_production = None
    return render_template("gallery.html", user=current_user, kittie_production=kittie_production)


@views.route('/sitemap.xml')
def serve_sitemap():
    return send_from_directory('static', 'sitemap.xml')
    

@views.route('/robots.txt')
def robots():
    return send_from_directory('static', 'robots.txt')


@corp.route('/website_terms_of_use')
def website_terms_of_use():
    kittie_production = None
    current_path = request.path
    referrer = request.referrer
    return render_template("corporate_pages/website_terms_of_use.html", user=current_user, current_path=current_path, referrer=referrer, kittie_production=kittie_production)


@corp.route('/our_impact')
def our_impact():
    kittie_production = None
    current_path = request.path
    referrer = request.referrer
    return render_template("corporate_pages/our_impact.html", user=current_user, current_path=current_path, referrer=referrer, kittie_production=kittie_production)


@corp.route('/legal_obligations')
@login_required
def legal_obligations():
    kittie_production = None
    current_path = request.path
    referrer = request.referrer
    return render_template("corporate_pages/legal_obligations.html", user=current_user, current_path=current_path, referrer=referrer, kittie_production=kittie_production)


@corp.route('/workplace_policies')
@login_required
def workplace_policies():
    kittie_production = None
    current_path = request.path
    referrer = request.referrer
    return render_template("corporate_pages/workplace_policies.html", user=current_user, current_path=current_path, referrer=referrer, kittie_production=kittie_production)


@views.route('/clear_all')   # Delete in production!!!!!!!!!!!!!!!!!!!!!
def clear_all():
    User.query.delete()
    UserAuditLog.query.delete()
    kittie_production_database.query.delete()
    ProductionAuditLog.query.delete()
    Permission.query.delete()
    PermissionAuditLog.query.delete()
    FileAuditLog.query.delete()
    FileAccessLog.query.delete()
    db.session.commit()
    return 'All data cleared!'


@views.route('/clear_audit')   # Delete in production!!!!!!!!!!!!!!!!!!!!!
def clear_audit():
    UserAuditLog.query.delete()
    ProductionAuditLog.query.delete()
    PermissionAuditLog.query.delete()
    FileAuditLog.query.delete()
    FileAccessLog.query.delete()
    db.session.commit()
    return 'Audit data cleared!'