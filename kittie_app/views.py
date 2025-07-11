import json
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, get_flashed_messages, current_app, session, abort
from flask_login import login_required, current_user
from kittie_app.models import db, User, kittie_production_database, Permission
from kittie_app.utils import generate_secure_token, send_welcome_email
from datetime import datetime
from sqlalchemy import or_
import re
from urllib.parse import urlencode
import os
import time
from werkzeug.utils import secure_filename, safe_join
import logging


views = Blueprint('views', __name__)


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


@views.route('/productions')
def productions():
    kittie_production = None
    return render_template("productions.html", user=current_user, kittie_production=kittie_production)


@views.route('/terms')
def terms():
    kittie_production = None
    current_path = request.path
    referrer = request.referrer
    return render_template("terms.html", user=current_user, current_path=current_path, referrer=referrer, kittie_production=kittie_production)


ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@views.route('/add_production', methods=['GET', 'POST'])
@login_required
def add_production():        
    kittie_production = None
    if request.method == 'POST':
        form_token = request.form.get('csrf_token')
        session_token = session.get('_csrf_token')

        if not form_token or form_token != session_token:
            abort(403)

        title = request.form.get("title")
        dist_format = request.form.get("distFormat")
        length = request.form.get("length")
        genre = request.form.getlist("genre")
        language = request.form.getlist("language")
        setting = request.form.get("setting")
        est_budget = request.form.get("estBudget")

        genre_str = ', '.join(genre)
        language_str = ', '.join(language)

        cover_file = request.files["coverFile"]
        if cover_file and allowed_file(cover_file.filename):
            c_filename = (f"{secure_filename(title)}_cover.jpeg").lower().replace(' ', '_')
            upload_folder = current_app.config['COVER_UPLOAD_FOLDER']
            cover_file.save(os.path.join(upload_folder, c_filename))
            cover_file_path = os.path.join('/static/covers', c_filename)

        one_sheet_file_path = None
        if 'oneSheetFile' in request.files:
            one_sheet_file = request.files["oneSheetFile"]
            if one_sheet_file and allowed_file(one_sheet_file.filename):
                new_os_filename = (f"{secure_filename(title)}_one_sheet").lower().replace(' ', '_')
                _, file_extension = os.path.splitext(one_sheet_file.filename)
                os_filename = f"{new_os_filename}{file_extension}"
                upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER']
                one_sheet_file.save(os.path.join(upload_folder, os_filename))
                one_sheet_file_path = os.path.join('/static/project_files', os_filename)

        pack_file_path = None
        if 'pitchFile' in request.files:
            pack_file = request.files["pitchFile"]
            if pack_file and allowed_file(pack_file.filename):
                new_pd_filename = (f"{secure_filename(title)}_pitch_deck").lower().replace(' ', '_')
                _, file_extension = os.path.splitext(pack_file.filename)
                pd_filename = f"{new_pd_filename}{file_extension}"
                upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER']
                pack_file.save(os.path.join(upload_folder, pd_filename))
                pack_file_path = os.path.join('/static/project_files', pd_filename)

        budget_file_path = None
        if 'budgetFile' in request.files:
            budget_file = request.files["budgetFile"]
            if budget_file and allowed_file(budget_file.filename):
                new_b_filename = (f"{secure_filename(title)}_budget").lower().replace(' ', '_')
                _, file_extension = os.path.splitext(budget_file.filename)
                b_filename = f"{new_b_filename}{file_extension}"
                upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER']
                budget_file.save(os.path.join(upload_folder, b_filename))
                budget_file_path = os.path.join('/static/project_files', b_filename)

        treatment_file_path = None
        if 'treatmentFile' in request.files:
            treatment_file = request.files["treatmentFile"]
            if treatment_file and allowed_file(treatment_file.filename):
                new_t_filename = (f"{secure_filename(title)}_treatment").lower().replace(' ', '_')
                _, file_extension = os.path.splitext(treatment_file.filename)
                t_filename = f"{new_t_filename}{file_extension}"
                upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER']
                treatment_file.save(os.path.join(upload_folder, t_filename))
                treatment_file_path = os.path.join('/static/project_files', t_filename)

        script_file_path = None
        if 'scriptFile' in request.files:
            script_file = request.files["scriptFile"]
            if script_file and allowed_file(script_file.filename):
                new_s_filename = (f"{secure_filename(title)}_script").lower().replace(' ', '_')
                _, file_extension = os.path.splitext(script_file.filename)
                s_filename = f"{new_s_filename}{file_extension}"
                upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER']
                script_file.save(os.path.join(upload_folder, s_filename))
                script_file_path = os.path.join('/static/project_files', s_filename)

        existing_production_with_title = kittie_production_database.query.filter_by(title=title).first()

        if existing_production_with_title:
            flash('Title already exists. Please choose a different title.', category='error')
        else:
            new_kittie_production = kittie_production_database(
                title=title,
                dist_format=dist_format,
                length=length,
                genre=genre_str,
                language=language_str,
                setting=setting,
                est_budget=est_budget,
                cover_file_path=cover_file_path,
                one_sheet_file_path=one_sheet_file_path,
                pack_file_path=pack_file_path,
                budget_file_path=budget_file_path,
                treatment_file_path=treatment_file_path,
                script_file_path=script_file_path,
                url = title.lower().replace(' ', '_')
            )
            db.session.add(new_kittie_production)
            db.session.commit()

        flash('Production added successfully', category='success')
        return redirect(url_for('views.kittie_productions', user_id=current_user.id, kittie_production=kittie_production))

    return render_template("add_production.html", user=current_user, kittie_production=kittie_production)


@views.route('/delete_production/<int:kittie_production_id>')
@login_required
def delete_production(kittie_production_id):
    kittie_production = kittie_production_database.query.get_or_404(kittie_production_id)
    db.session.delete(kittie_production)
    db.session.commit()
    flash('Production deleted successfully.', category='success')

    return redirect(url_for("views.kittie_productions", user=current_user))


@views.route('/kittie_productions', methods=['GET'])
@login_required
def kittie_productions():
    users = User.query.all()
    permissions = Permission.query.all()
    filter_option = request.args.get('filter-box')
    if filter_option == 'all':
        kittie_productions = kittie_production_database.query.all()
    elif filter_option == 'Feature Film':
        kittie_productions = kittie_production_database.query.filter_by(dist_format='Feature Film').all()
    elif filter_option == 'Television Drama':
        kittie_productions = kittie_production_database.query.filter_by(dist_format='Television Drama').all()
    elif filter_option == 'Co-production':
        kittie_productions = kittie_production_database.query.filter_by(dist_format='Co-production').all()
    elif filter_option == 'Action':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Action%')).all()
    elif filter_option == 'Biopic':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Biopic%')).all()
    elif filter_option == 'Comedy':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Comedy%')).all()
    elif filter_option == 'Crime':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Crime%')).all()
    elif filter_option == 'Period':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Historic%')).all()
    elif filter_option == 'Horror':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Horror%')).all()
    elif filter_option == 'Romance':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Romance%')).all()
    elif filter_option == 'Thriller':
        kittie_productions = kittie_production_database.query.filter(kittie_production_database.genre.ilike('%Thriller%')).all()
    elif filter_option is None or filter_option == 'all':
        kittie_productions = kittie_production_database.query.all()
    else:
        flash('Invalid filter option', category='error')
        return redirect(request.url)
    kittie_production = None
    return render_template("kittie_productions.html", user=current_user, kittie_productions=kittie_productions, kittie_production=kittie_production, permissions=permissions)


@views.route('/kittie_production_details/<url>')
@login_required
def kittie_production_details(url):
    kittie_production = kittie_production_database.query.filter_by(url=url).first_or_404()
    return render_template("kittie_production_details.html", user=current_user, kittie_production=kittie_production, url_for=url_for)


@views.route('/view_users', methods=["GET", "POST"])
@login_required
def view_users():
    kittie_production = None
    kittie_productions_list = kittie_production_database.query.all()
    current_auth_level = current_user.auth_level
    users = User.query.all()
    permissions = Permission.query.all()

    if request.method == "POST":
        submitted_user_ids = {int(name.split('_')[0]) for name in request.form if '_' in name}

        if submitted_user_ids:
            user_id = next(iter(submitted_user_ids))
            user = User.query.get(user_id)

            if user:
                for each_production in kittie_productions_list:
                    checkbox_name = f"{user.id}_{each_production.id}"
                    production_permission = Permission.query.filter_by(
                        user_id=user.id, 
                        kittie_production_database_id=each_production.id
                    ).first()

                    if checkbox_name in request.form:
                        if production_permission is None:
                            production_permission = Permission(
                                user_id=user.id,
                                kittie_production_database_id=each_production.id,
                                can_view=True
                            )
                        production_permission.can_view = True
                        db.session.add(production_permission)
                    else:
                        if production_permission:
                            db.session.delete(production_permission)

                db.session.commit()
                flash(f'Permissions updated successfully for {user.first_name} {user.last_name}!', 'success')

        return redirect(url_for('views.view_users'))

    sort_option = request.args.get('sort_option')
    if sort_option == 'name_asc':
        users = sorted(users, key=lambda u: u.first_name)
    elif sort_option == 'name_desc':
        users = sorted(users, key=lambda u: u.first_name, reverse=True)

    return render_template('view_users.html', user=current_user, users=users, kittie_production=kittie_production, kittie_productions_list=kittie_productions_list, permissions=permissions)



@views.route('/add_user', methods=["GET", "POST"])
@login_required
def add_user():
    kittie_production = None
    if request.method == "POST":
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        if not re.match(email_pattern, email):
            flash('Invalid email address.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        else:
            auth_level = User.get_auth_level(email)

            token = generate_secure_token()

            new_user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                auth_level=auth_level,
                password_reset_token=token
            )

            db.session.add(new_user)
            db.session.commit()
            
            send_welcome_email(email, token, first_name)

            return redirect(url_for('views.view_users', user_id=current_user.id, kittie_production=kittie_production))
        
    return render_template("add_user.html", user=current_user, kittie_production=kittie_production)


@views.route('/edit_user/<int:user_id>', methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    kittie_production = None
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        new_email = request.form.get("email")
        if new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                flash("Email already exists. Please choose a different email.", category="error")
                return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))
        user.email=new_email
        user.first_name=request.form.get("firstName")
        user.last_name=request.form.get("lastName")
        db.session.commit()
        flash("User details updated successfully.", category="success")
        return redirect(url_for('views.view_users', user_id=user.id, kittie_production=kittie_production))
        
    return render_template("edit_user.html", user=user, kittie_production=kittie_production)


@views.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    kittie_production = None
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', category='success')

    return redirect(url_for("views.view_users", user_id=user.id, kittie_production=kittie_production))