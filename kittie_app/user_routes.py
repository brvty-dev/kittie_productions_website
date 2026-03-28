from flask import Blueprint, render_template, request, flash, redirect, url_for, session, abort
from flask_login import login_required, current_user
from kittie_app.models import db, User, kittie_production_database, ProductionAuditLog, Permission, UserAuditLog, PermissionAuditLog, FileAuditLog, FileAccessLog
from kittie_app.utils import generate_secure_token, send_welcome_email
from sqlalchemy import or_
import re
import os


users = Blueprint('users', __name__)


@users.route('/view_users', methods=["GET", "POST"])
@login_required
def view_users():
    kittie_production = None

    if current_user.auth_level == 3:
        abort(403)

    kittie_productions_list = kittie_production_database.query.order_by(
        kittie_production_database.title.asc()
    ).all()
    users = User.query.all()

    if request.method == "POST":
        user_id = request.form.get("user_id", type=int)
        user = User.query.get_or_404(user_id)

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
                    db.session.add(production_permission)

                else:
                    production_permission.can_view = True

                audit = PermissionAuditLog(
                    target_user_id=user.id,
                    kittie_production_database_id=each_production.id,
                    action="granted",
                    admin_email_snapshot=current_user.email
                )
                db.session.add(audit)

            else:

                if production_permission and production_permission.can_view:
                    production_permission.can_view = False

                    audit = PermissionAuditLog(
                        target_user_id=user.id,
                        kittie_production_database_id=each_production.id,
                        action="revoked",
                        admin_email_snapshot=current_user.email
                    )
                    db.session.add(audit)

        db.session.commit()
        flash(
            f'Permissions updated successfully for {user.first_name} {user.last_name}!',
            'success'
        )
        return redirect(url_for('users.view_users'))

    sort_option = request.args.get('sort_option')
    if sort_option == 'name_asc':
        users = sorted(users, key=lambda u: u.first_name)
    elif sort_option == 'name_desc':
        users = sorted(users, key=lambda u: u.first_name, reverse=True)

    permissions = Permission.query.all()
    permission_map = {
        (perm.user_id, perm.kittie_production_database_id): perm.can_view
        for perm in permissions
    }

    return render_template(
        "user_pages/view_users.html",
        user=current_user,
        users=users,
        kittie_production=kittie_production,
        kittie_productions_list=kittie_productions_list,
        permission_map=permission_map
    )


@users.route('/add_user', methods=["GET", "POST"])
@login_required
def add_user():
    if current_user.auth_level == 3:
        abort(403)

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
                created_by_user_id=current_user.id,
                updated_by_user_id=current_user.id,
                password_reset_token=token
            )

            db.session.add(new_user)
            db.session.flush()

            audit_log = UserAuditLog(
                actor_user_id=current_user.id,
                target_user_id=new_user.id,
                action='added',
                actor_email_snapshot=current_user.email,
                target_email_snapshot=new_user.email,
                target_first_name_snapshot=new_user.first_name,
                target_last_name_snapshot=new_user.last_name
            )

            db.session.add(audit_log)
            db.session.commit()
            
            send_welcome_email(email, token, first_name)
            flash('User added successfully.', category='success')

            return redirect(url_for('users.view_users', user_id=current_user.id, kittie_production=kittie_production))
        
    return render_template("user_pages/add_user.html", user=current_user, kittie_production=kittie_production)


@users.route('/edit_user/<int:user_id>', methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if current_user.auth_level == 3:
        abort(403)

    kittie_production = None
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        new_email = request.form.get("email")
        new_first_name = request.form.get("firstName")
        new_last_name = request.form.get("lastName")

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'

        if not new_email:
            flash("Email is required.", category="error")
            return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        if not re.match(email_pattern, new_email):
            flash("Invalid email address.", category="error")
            return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        if len(new_first_name) < 2:
            flash("First name must be greater than 1 character.", category="error")
            return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        if len(new_last_name) < 2:
            flash("Last name must be greater than 1 character.", category="error")
            return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        if new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                flash("Email already exists. Please choose a different email.", category="error")
                return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        changed = (
            new_email != user.email or
            new_first_name != user.first_name or
            new_last_name != user.last_name
        )

        if not changed:
            flash("No changes made.", category="info")
            return redirect(url_for('views.edit_user', user_id=user.id, kittie_production=kittie_production))

        old_email = user.email
        old_first_name = user.first_name
        old_last_name = user.last_name

        user.email=new_email
        user.first_name = new_first_name
        user.last_name = new_last_name
        user.updated_by_user_id = current_user.id

        audit_log = UserAuditLog(
            actor_user_id=current_user.id,
            target_user_id=user.id,
            action='updated',
            actor_email_snapshot=current_user.email,
            target_email_snapshot=new_email,
            target_first_name_snapshot=new_first_name,
            target_last_name_snapshot=new_last_name,
            old_email=old_email,
            new_email=new_email,
            old_first_name=old_first_name,
            new_first_name=new_first_name,
            old_last_name=old_last_name,
            new_last_name=new_last_name
        )

        db.session.add(audit_log)
        db.session.commit()

        flash("User details updated successfully.", category="success")
        return redirect(url_for('users.view_users', user_id=user.id, kittie_production=kittie_production))
        
    return render_template("user_pages/edit_user.html", user=user, kittie_production=kittie_production)


@users.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    audit_log = UserAuditLog(
        target_user_id=user.id,
        target_email_snapshot=user.email,
        action="deleted",
        actor_user_id=current_user.id,
        actor_email_snapshot=current_user.email,
        new_first_name=None,
        new_last_name=None
    )
    db.session.add(audit_log)

    User.query.filter_by(created_by_user_id=user.id).update(
        {User.created_by_user_id: None},
        synchronize_session=False
    )

    User.query.filter_by(updated_by_user_id=user.id).update(
        {User.updated_by_user_id: None},
        synchronize_session=False
    )

    db.session.flush()
    db.session.delete(user)
    db.session.commit()

    flash("User deleted successfully.", "success")
    return redirect(url_for("users.view_users"))


@users.route('/user_audit/<int:user_id>')
@login_required
def user_audit(user_id):
    kittie_production = None
    referrer = request.referrer

    if current_user.auth_level != 1:
        abort(403)

    selected_user = User.query.get_or_404(user_id)

    kittie_productions_list = kittie_production_database.query.order_by(
        kittie_production_database.title.asc()
    ).all()

    permission_map = {
        perm.kittie_production_database_id: perm
        for perm in selected_user.user_permissions
    }

    permission_audits = PermissionAuditLog.query.filter_by(
        target_user_id=selected_user.id
    ).order_by(
        PermissionAuditLog.created_at.desc()
    ).all()

    permission_audit_map = {}

    for audit in permission_audits:
        production_id = audit.kittie_production_database_id
        if production_id not in permission_audit_map:
            permission_audit_map[production_id] = []
        permission_audit_map[production_id].append(audit)

    file_access_logs = FileAccessLog.query.filter_by(
        user_id=selected_user.id
    ).order_by(FileAccessLog.created_at.desc()).all()

    file_access_map = {}

    for log in file_access_logs:
        if log.production_id not in file_access_map:
            file_access_map[log.production_id] = []
        file_access_map[log.production_id].append(log)

    return render_template(
        "user_pages/user_audit.html",
        user=current_user,
        selected_user=selected_user,
        kittie_production=kittie_production,
        kittie_productions_list=kittie_productions_list,
        permission_map=permission_map,
        permission_audit_map=permission_audit_map,
        file_access_map=file_access_map,
        referrer=referrer
    )


@users.route('/production_audit/<int:kittie_production_id>')
@login_required
def production_audit(kittie_production_id):
    kittie_production = None
    referrer = request.referrer

    if current_user.auth_level != 1:
        abort(403)

    selected_production = kittie_production_database.query.get_or_404(kittie_production_id)

    live_permissions = (
        Permission.query
        .filter_by(kittie_production_database_id=selected_production.id)
        .order_by(Permission.updated_at.desc())
        .all()
    )

    current_permission_map = {}
    for perm in live_permissions:
        current_permission_map[perm.user_id] = perm

    production_audits = ProductionAuditLog.query.filter_by(
        production_id=selected_production.id
    ).order_by(ProductionAuditLog.created_at.desc()).all()

    permission_audits = PermissionAuditLog.query.filter_by(
        kittie_production_database_id=selected_production.id
    ).order_by(PermissionAuditLog.created_at.desc()).all()

    file_audits = FileAuditLog.query.filter_by(
        production_id=selected_production.id
    ).order_by(FileAuditLog.created_at.desc()).all()

    file_access_logs = FileAccessLog.query.filter_by(
        production_id=selected_production.id
    ).order_by(FileAccessLog.created_at.desc()).all()

    permission_audit_map = {}
    for audit in permission_audits:
        key = audit.target_user_id or audit.target_email_snapshot or "deleted_user"
        permission_audit_map.setdefault(key, []).append(audit)

    file_access_map = {}
    for log in file_access_logs:
        key = log.user_id or log.user_email_snapshot or "deleted_user"
        file_access_map.setdefault(key, []).append(log)

    file_audit_map = {}
    for audit in file_audits:
        file_audit_map.setdefault(audit.file_type, []).append(audit)

    return render_template(
        "user_pages/production_audit.html",
        user=current_user,
        kittie_production=kittie_production,
        selected_production=selected_production,
        live_permissions=live_permissions,
        current_permission_map=current_permission_map,
        production_audits=production_audits,
        permission_audits=permission_audits,
        permission_audit_map=permission_audit_map,
        file_audits=file_audits,
        file_audit_map=file_audit_map,
        file_access_logs=file_access_logs,
        file_access_map=file_access_map,
        referrer=referrer
    )


@users.route('/audit_overview')
@login_required
def audit_overview():
    if current_user.auth_level != 1:
        abort(403)
    referrer = request.referrer

    user_audits = UserAuditLog.query.order_by(UserAuditLog.created_at.desc()).all()
    production_audits = ProductionAuditLog.query.order_by(ProductionAuditLog.created_at.desc()).all()
    permission_audits = PermissionAuditLog.query.order_by(PermissionAuditLog.created_at.desc()).all()
    file_audits = FileAuditLog.query.order_by(FileAuditLog.created_at.desc()).all()
    file_access_logs = FileAccessLog.query.order_by(FileAccessLog.created_at.desc()).all()

    return render_template(
        "user_pages/audit_overview.html",
        user=current_user,
        kittie_production=None,
        user_audits=user_audits,
        production_audits=production_audits,
        permission_audits=permission_audits,
        file_audits=file_audits,
        file_access_logs=file_access_logs,
        referrer=referrer
    )