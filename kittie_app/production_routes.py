from flask import Blueprint, render_template, request, flash, redirect, send_file, url_for, current_app, session, abort, send_from_directory, after_this_request
from flask_login import login_required, current_user
from kittie_app.models import db, User, kittie_production_database, ProductionAuditLog, Permission, FileAuditLog, FileAccessLog
from kittie_app.utils import save_uploaded_file, get_temp_watermarks_dir, create_watermarked_pdf, build_watermark_data, cleanup_temp_watermarks_if_due
from datetime import datetime, timezone
from sqlalchemy import or_
import os
import time
import hashlib
import os
import uuid
import secrets


prod = Blueprint('prod', __name__)


@prod.route('/add_production', methods=['GET', 'POST'])
@login_required
def add_production():
    if current_user.auth_level == 3:
        abort(403)
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
        production_url = title.lower().replace(' ', '_')

        existing_production_with_title = kittie_production_database.query.filter_by(title=title).first()
        if existing_production_with_title:
            flash('Title already exists. Please choose a different title.', category='error')
            return redirect(url_for('prod.add_production'))
        
        project_upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER_ABS']

        file_fields = {
            "coverFile": "cover",
            "oneSheetFile": "one_sheet",
            "twoSheetFile": "two_sheet",
            "pitchFile": "pitch_deck",
            "budgetFile": "budget",
            "treatmentFile": "treatment",
            "scriptFile": "script",
        }

        saved_files = {}

        for form_field, suffix in file_fields.items():
            saved_files[form_field] = save_uploaded_file(
                request.files.get(form_field),
                project_upload_folder,
                title,
                suffix
            )

        new_kittie_production = kittie_production_database(
            title=title,
            dist_format=dist_format,
            length=length,
            genre=genre_str,
            language=language_str,
            setting=setting,
            est_budget=est_budget,
            cover_file_path=saved_files["coverFile"],
            one_sheet_file_path=saved_files["oneSheetFile"],
            two_sheet_file_path=saved_files["twoSheetFile"],
            pitch_deck_file_path=saved_files["pitchFile"],
            budget_file_path=saved_files["budgetFile"],
            treatment_file_path=saved_files["treatmentFile"],
            script_file_path=saved_files["scriptFile"],
            cover_file_version=1 if saved_files["coverFile"] else None,
            one_sheet_file_version=1 if saved_files["oneSheetFile"] else None,
            two_sheet_file_version=1 if saved_files["twoSheetFile"] else None,
            pitch_deck_file_version=1 if saved_files["pitchFile"] else None,
            budget_file_version=1 if saved_files["budgetFile"] else None,
            treatment_file_version=1 if saved_files["treatmentFile"] else None,
            script_file_version=1 if saved_files["scriptFile"] else None,
            url=production_url,
            created_by_user_id=current_user.id,
            updated_by_user_id=current_user.id
        )

        db.session.add(new_kittie_production)
        db.session.flush()

        production_audit_log = ProductionAuditLog(
            actor_user_id=current_user.id,
            production_id=new_kittie_production.id,
            action='added',
            actor_email_snapshot=current_user.email,
            production_title_snapshot=title,
            changed_fields='title,dist_format,length,genre,language,setting,est_budget,url',
            old_title=None,
            new_title=title,
            old_dist_format=None,
            new_dist_format=dist_format,
            old_length=None,
            new_length=length,
            old_genre=None,
            new_genre=genre_str,
            old_language=None,
            new_language=language_str,
            old_setting=None,
            new_setting=setting,
            old_est_budget=None,
            new_est_budget=est_budget,
            old_url=None,
            new_url=production_url
        )
        db.session.add(production_audit_log)

        for form_field, file_type in file_fields.items():
            saved_path = saved_files.get(form_field)

            if saved_path:
                absolute_path = os.path.join(project_upload_folder, saved_path)

                file_hash = None
                file_size = None

                if os.path.exists(absolute_path):
                    with open(absolute_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    file_size = os.path.getsize(absolute_path)

                file_audit_log = FileAuditLog(
                    production_id=new_kittie_production.id,
                    actor_user_id=current_user.id,
                    file_type=file_type,
                    action='added',
                    old_filename=None,
                    new_filename=os.path.basename(saved_path),
                    file_hash=file_hash,
                    file_size=file_size,
                    actor_email_snapshot=current_user.email,
                    production_title_snapshot=title
                )
                db.session.add(file_audit_log)

        db.session.commit()

        flash('Production added successfully', category='success')
        return redirect(url_for('prod.kittie_productions', user_id=current_user.id, kittie_production=kittie_production))

    return render_template("production_pages/add_production.html", user=current_user, kittie_production=kittie_production)


@prod.route('/edit_production/<int:kittie_production_id>', methods=['GET', 'POST'])
@login_required
def edit_production(kittie_production_id):

    if current_user.auth_level != 1:
        abort(403)

    kittie_production = kittie_production_database.query.get_or_404(kittie_production_id)

    if request.method == 'POST':

        form_token = request.form.get('csrf_token')
        session_token = session.get('_csrf_token')

        if not form_token or form_token != session_token:
            abort(403)

        # Existing values
        old_dist_format = kittie_production.dist_format
        old_length = kittie_production.length
        old_genre = kittie_production.genre
        old_language = kittie_production.language
        old_setting = kittie_production.setting
        old_est_budget = kittie_production.est_budget

        # Submitted values
        submitted_dist_format = request.form.get("distFormat")
        submitted_length = request.form.get("length")
        submitted_setting = request.form.get("setting")
        submitted_est_budget = request.form.get("estBudget")

        new_dist_format = submitted_dist_format.strip() if submitted_dist_format else old_dist_format
        new_length = submitted_length.strip() if submitted_length else old_length
        new_setting = submitted_setting.strip() if submitted_setting else old_setting
        new_est_budget = submitted_est_budget.strip() if submitted_est_budget else old_est_budget

        submitted_genre_list = [g.strip() for g in request.form.getlist("genre") if g and g.strip()]
        submitted_language_list = [l.strip() for l in request.form.getlist("language") if l and l.strip()]

        new_genre = ', '.join(submitted_genre_list) if submitted_genre_list else old_genre
        new_language = ', '.join(submitted_language_list) if submitted_language_list else old_language

        changed_fields = []

        if old_dist_format != new_dist_format:
            changed_fields.append("dist_format")

        if old_length != new_length:
            changed_fields.append("length")

        if old_genre != new_genre:
            changed_fields.append("genre")

        if old_language != new_language:
            changed_fields.append("language")

        if old_setting != new_setting:
            changed_fields.append("setting")

        if old_est_budget != new_est_budget:
            changed_fields.append("est_budget")

        project_upload_folder = current_app.config['PROJECT_FILES_UPLOAD_FOLDER_ABS']

        file_fields = {
            "coverFile": {
                "file_type": "cover",
                "path_attr": "cover_file_path",
                "version_attr": "cover_file_version",
                "remove_flag": "remove_cover_file"
            },
            "oneSheetFile": {
                "file_type": "one_sheet",
                "path_attr": "one_sheet_file_path",
                "version_attr": "one_sheet_file_version",
                "remove_flag": "remove_one_sheet_file"
            },
            "twoSheetFile": {
                "file_type": "two_sheet",
                "path_attr": "two_sheet_file_path",
                "version_attr": "two_sheet_file_version",
                "remove_flag": "remove_two_sheet_file"
            },
            "pitchFile": {
                "file_type": "pitch_deck",
                "path_attr": "pitch_deck_file_path",
                "version_attr": "pitch_deck_file_version",
                "remove_flag": "remove_pitch_deck_file"
            },
            "budgetFile": {
                "file_type": "budget",
                "path_attr": "budget_file_path",
                "version_attr": "budget_file_version",
                "remove_flag": "remove_budget_file"
            },
            "treatmentFile": {
                "file_type": "treatment",
                "path_attr": "treatment_file_path",
                "version_attr": "treatment_file_version",
                "remove_flag": "remove_treatment_file"
            },
            "scriptFile": {
                "file_type": "script",
                "path_attr": "script_file_path",
                "version_attr": "script_file_version",
                "remove_flag": "remove_script_file"
            },
        }

        file_changes_made = False

        for form_field, config in file_fields.items():

            uploaded_file = request.files.get(form_field)
            remove_requested = request.form.get(config["remove_flag"]) == "1"

            current_path = getattr(kittie_production, config["path_attr"])
            current_version = getattr(kittie_production, config["version_attr"]) or 0

            if remove_requested and current_path:

                abs_path = os.path.join(project_upload_folder, current_path)

                if os.path.exists(abs_path):
                    os.remove(abs_path)

                setattr(kittie_production, config["path_attr"], None)
                setattr(kittie_production, config["version_attr"], None)

                db.session.add(FileAuditLog(
                    production_id=kittie_production.id,
                    actor_user_id=current_user.id,
                    file_type=config["file_type"],
                    action='removed',
                    old_filename=os.path.basename(current_path),
                    new_filename=None,
                    file_hash=None,
                    file_size=None,
                    actor_email_snapshot=current_user.email,
                    production_title_snapshot=kittie_production.title
                ))

                file_changes_made = True
                changed_fields.append(config["file_type"])

            elif uploaded_file and uploaded_file.filename:

                saved_path = save_uploaded_file(
                    uploaded_file,
                    project_upload_folder,
                    kittie_production.title,
                    config["file_type"]
                )

                new_abs_path = os.path.join(project_upload_folder, saved_path)

                file_hash = None
                file_size = None

                if os.path.exists(new_abs_path):
                    with open(new_abs_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                    file_size = os.path.getsize(new_abs_path)

                new_version = current_version + 1 if current_path else 1

                setattr(kittie_production, config["path_attr"], saved_path)
                setattr(kittie_production, config["version_attr"], new_version)

                db.session.add(FileAuditLog(
                    production_id=kittie_production.id,
                    actor_user_id=current_user.id,
                    file_type=config["file_type"],
                    action='replaced' if current_path else 'added',
                    old_filename=os.path.basename(current_path) if current_path else None,
                    new_filename=os.path.basename(saved_path),
                    file_hash=file_hash,
                    file_size=file_size,
                    actor_email_snapshot=current_user.email,
                    production_title_snapshot=kittie_production.title
                ))

                file_changes_made = True
                changed_fields.append(config["file_type"])

        metadata_changed = any([
            old_dist_format != new_dist_format,
            old_length != new_length,
            old_genre != new_genre,
            old_language != new_language,
            old_setting != new_setting,
            old_est_budget != new_est_budget
        ])

        if not metadata_changed and not file_changes_made:
            flash('No changes made.', category='info')
            return redirect(url_for('prod.edit_production', kittie_production_id=kittie_production.id))

        # Update metadata
        kittie_production.dist_format = new_dist_format
        kittie_production.length = new_length
        kittie_production.genre = new_genre
        kittie_production.language = new_language
        kittie_production.setting = new_setting
        kittie_production.est_budget = new_est_budget
        kittie_production.updated_by_user_id = current_user.id

        db.session.add(ProductionAuditLog(
            actor_user_id=current_user.id,
            production_id=kittie_production.id,
            action='updated',
            actor_email_snapshot=current_user.email,
            production_title_snapshot=kittie_production.title,
            changed_fields=",".join(dict.fromkeys(changed_fields)),
            old_dist_format=old_dist_format,
            new_dist_format=new_dist_format,
            old_length=old_length,
            new_length=new_length,
            old_genre=old_genre,
            new_genre=new_genre,
            old_language=old_language,
            new_language=new_language,
            old_setting=old_setting,
            new_setting=new_setting,
            old_est_budget=old_est_budget,
            new_est_budget=new_est_budget
        ))

        db.session.commit()

        flash('Production updated successfully.', category='success')

        return redirect(url_for('prod.kittie_production_details', url=kittie_production.url))

    return render_template(
        "production_pages/edit_production.html", user=current_user, kittie_production=kittie_production)


@prod.route('/delete_production/<int:kittie_production_id>')
@login_required
def delete_production(kittie_production_id):
    if current_user.auth_level != 1:
        abort(403)

    kittie_production = kittie_production_database.query.get_or_404(kittie_production_id)

    old_title = kittie_production.title
    old_dist_format = kittie_production.dist_format
    old_length = kittie_production.length
    old_genre = kittie_production.genre
    old_language = kittie_production.language
    old_setting = kittie_production.setting
    old_est_budget = kittie_production.est_budget
    old_url = kittie_production.url

    production_audit = ProductionAuditLog(
        actor_user_id=current_user.id,
        production_id=kittie_production.id,
        action='removed',
        actor_email_snapshot=current_user.email,
        production_title_snapshot=old_title,
        changed_fields='title,dist_format,length,genre,language,setting,est_budget,url',
        old_title=old_title,
        new_title=None,
        old_dist_format=old_dist_format,
        new_dist_format=None,
        old_length=old_length,
        new_length=None,
        old_genre=old_genre,
        new_genre=None,
        old_language=old_language,
        new_language=None,
        old_setting=old_setting,
        new_setting=None,
        old_est_budget=old_est_budget,
        new_est_budget=None,
        old_url=old_url,
        new_url=None
    )

    db.session.add(production_audit)
    db.session.delete(kittie_production)
    db.session.commit()

    flash('Production deleted successfully.', category='success')

    return redirect(url_for("prod.kittie_productions", user=current_user))


@prod.route('/kittie_productions', methods=['GET'])
@login_required
def kittie_productions():
    cleanup_temp_watermarks_if_due()
    users = User.query.all()
    permissions = Permission.query.all()
    filter_option = request.args.get('filter-box')
    referrer = request.referrer
    if filter_option == 'all':
        kittie_productions = kittie_production_database.query.all()
    elif filter_option == 'Feature Film':
        kittie_productions = kittie_production_database.query.filter_by(dist_format='Feature Film').all()
    elif filter_option == 'Short Film':
        kittie_productions = kittie_production_database.query.filter_by(dist_format='Short Film').all()
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
    return render_template("production_pages/kittie_productions.html", user=current_user, kittie_productions=kittie_productions, kittie_production=kittie_production, permissions=permissions, referrer=referrer)


@prod.route('/kittie_production_details/<url>')
@login_required
def kittie_production_details(url):
    kittie_production = kittie_production_database.query.filter_by(url=url).first_or_404()
    return render_template("production_pages/kittie_production_details.html", user=current_user, kittie_production=kittie_production)


@prod.route("/productions/<string:prod_url>/<string:file_type>/v<int:version>")
@login_required
def production_file(prod_url, file_type, version):
    kittie_production = kittie_production_database.query.filter_by(url=prod_url).first_or_404()
    current_auth_level = current_user.auth_level

    if current_auth_level == 3:
        perm = Permission.query.filter_by(
                user_id=current_user.id,
                kittie_production_database_id=kittie_production.id,
                can_view=True
            ).first()
        if not perm:
                abort(403)

    field_map = {
        "cover": "cover_file_path",
        "one_sheet": "one_sheet_file_path",
        "two_sheet": "two_sheet_file_path",
        "pitch_deck": "pitch_deck_file_path",
        "budget": "budget_file_path",
        "treatment": "treatment_file_path",
        "script": "script_file_path",
    }

    if file_type not in field_map:
        abort(404)

    stored_file_path = getattr(kittie_production, field_map[file_type])
    if not stored_file_path:
        abort(404)

    folder = current_app.config["PROJECT_FILES_UPLOAD_FOLDER_ABS"]
    relative_filename = stored_file_path.replace("/static/project_files/", "").lstrip("/")
    source_file_path = os.path.join(folder, relative_filename)

    if not os.path.exists(source_file_path):
        abort(404)

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    if file_type == "cover":
        try:
            access_log = FileAccessLog(
                user_id=current_user.id,
                production_id=kittie_production.id,
                file_type=file_type,
                filename=relative_filename,
                file_version=version,
                action="viewed",
                created_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=request.user_agent.string,
                watermark_lines=None,
                watermark_token=None,
                user_email_snapshot=current_user.email,
                production_title_snapshot=kittie_production.title
            )

            db.session.add(access_log)
            db.session.commit()

            return send_from_directory(folder, relative_filename, as_attachment=False)

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to log cover file view.")
            abort(500)

    if not source_file_path.lower().endswith(".pdf"):
        abort(400)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    watermark_token = secrets.token_urlsafe(16)

    watermark_lines, watermark_config = build_watermark_data(
        file_type=file_type,
        version=version,
        user_email=current_user.email,
        timestamp=timestamp
    )

    temp_folder = get_temp_watermarks_dir()

    output_filename = f"{uuid.uuid4().hex}_{os.path.basename(source_file_path)}"
    output_pdf_path = os.path.join(temp_folder, output_filename)

    try:
        create_watermarked_pdf(
            input_pdf_path=source_file_path,
            output_pdf_path=output_pdf_path,
            watermark_lines=watermark_lines,
            config=watermark_config
        )

        access_log = FileAccessLog(
            user_id=current_user.id,
            production_id=kittie_production.id,
            file_type=file_type,
            filename=relative_filename,
            file_version=version,
            action="viewed",
            created_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=request.user_agent.string,
            watermark_lines="\n".join(watermark_lines),
            watermark_token=watermark_token,
            user_email_snapshot=current_user.email,
            production_title_snapshot=kittie_production.title
        )

        db.session.add(access_log)
        db.session.commit()

        return send_file(
            output_pdf_path,
            as_attachment=False,
            mimetype="application/pdf"
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to watermark or log PDF view.")
        abort(500)


@prod.route("/productions/<string:prod_url>/<string:file_type>/v<int:version>/download")
@login_required
def download_production_file(prod_url, file_type, version):
    kittie_production = kittie_production_database.query.filter_by(url=prod_url).first_or_404()

    current_auth_level = current_user.auth_level

    if current_auth_level == 3:
        perm = Permission.query.filter_by(
            user_id=current_user.id,
            kittie_production_database_id=kittie_production.id,
            can_view=True
        ).first()
        if not perm:
            abort(403)

    field_map = {
        "cover": "cover_file_path",
        "one_sheet": "one_sheet_file_path",
        "two_sheet": "two_sheet_file_path",
        "pitch_deck": "pitch_deck_file_path",
        "budget": "budget_file_path",
        "treatment": "treatment_file_path",
        "script": "script_file_path",
    }

    if file_type not in field_map:
        abort(404)

    stored_file_path = getattr(kittie_production, field_map[file_type])
    if not stored_file_path:
        abort(404)

    project_upload_folder = current_app.config["PROJECT_FILES_UPLOAD_FOLDER_ABS"]
    relative_filename = stored_file_path.replace("/static/project_files/", "").lstrip("/")
    source_file_path = os.path.join(project_upload_folder, relative_filename)

    if not os.path.exists(source_file_path):
        abort(404)

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip_address and "," in ip_address:
        ip_address = ip_address.split(",")[0].strip()

    if file_type == "cover":
        try:
            access_log = FileAccessLog(
                user_id=current_user.id,
                production_id=kittie_production.id,
                file_type=file_type,
                filename=relative_filename,
                file_version=version,
                action="downloaded",
                created_at=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=request.user_agent.string,
                watermark_lines=None,
                watermark_token=None,
                user_email_snapshot=current_user.email,
                production_title_snapshot=kittie_production.title
            )

            db.session.add(access_log)
            db.session.commit()

            return send_file(
                source_file_path,
                as_attachment=True,
                download_name=os.path.basename(source_file_path)
            )

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to log cover file download.")
            abort(500)

    if not source_file_path.lower().endswith(".pdf"):
        abort(400)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    watermark_token = secrets.token_urlsafe(16)

    watermark_lines, watermark_config = build_watermark_data(
        file_type=file_type,
        version=version,
        user_email=current_user.email,
        timestamp=timestamp
    )

    temp_folder = get_temp_watermarks_dir()

    output_filename = f"{uuid.uuid4().hex}_{os.path.basename(source_file_path)}"
    output_pdf_path = os.path.join(temp_folder, output_filename)

    try:
        create_watermarked_pdf(
            input_pdf_path=source_file_path,
            output_pdf_path=output_pdf_path,
            watermark_lines=watermark_lines,
            config=watermark_config
        )

        access_log = FileAccessLog(
            user_id=current_user.id,
            production_id=kittie_production.id,
            file_type=file_type,
            filename=relative_filename,
            file_version=version,
            action="downloaded",
            created_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=request.user_agent.string,
            watermark_lines="\n".join(watermark_lines),
            watermark_token=watermark_token,
            user_email_snapshot=current_user.email,
            production_title_snapshot=kittie_production.title
        )

        db.session.add(access_log)
        db.session.commit()

        return send_file(
            output_pdf_path,
            as_attachment=True,
            download_name=os.path.basename(source_file_path),
            mimetype="application/pdf"
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to watermark or log PDF download.")
        abort(500)