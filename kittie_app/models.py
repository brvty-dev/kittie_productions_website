from . import db
from kittie_app.utils import utc_now
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """
    Class defining the model for the User database.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    auth_level = db.Column(db.Integer, nullable=False)
    password_reset_token = db.Column(db.String(150), unique=True, nullable=True)
    password_updated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    user_permissions = db.relationship(
        "Permission",
        backref="user",
        cascade="all, delete",
        lazy=True
    )

    created_by_user = db.relationship(
        "User",
        remote_side=[id],
        foreign_keys=[created_by_user_id],
        backref="users_created",
        passive_deletes=True
    )

    updated_by_user = db.relationship(
        "User",
        remote_side=[id],
        foreign_keys=[updated_by_user_id],
        backref="users_updated",
        passive_deletes=True
    )

    permissions_granted_or_removed = db.relationship(
        "PermissionAuditLog",
        foreign_keys="PermissionAuditLog.admin_user_id",
        backref="admin_user",
        lazy=True
    )

    permission_changes_received = db.relationship(
        "PermissionAuditLog",
        foreign_keys="PermissionAuditLog.target_user_id",
        backref="target_user",
        lazy=True
    )

    file_actions = db.relationship(
        "FileAuditLog",
        foreign_keys="FileAuditLog.actor_user_id",
        backref="actor_user",
        lazy=True
    )

    file_access_events = db.relationship(
        "FileAccessLog",
        foreign_keys="FileAccessLog.user_id",
        backref="access_user",
        lazy=True
    )

    productions_created = db.relationship(
        "kittie_production_database",
        foreign_keys="kittie_production_database.created_by_user_id",
        backref="created_by_user",
        lazy=True
    )

    production_actions = db.relationship(
        "ProductionAuditLog",
        foreign_keys="ProductionAuditLog.actor_user_id",
        backref="actor_user",
        lazy=True
    )

    productions_updated = db.relationship(
        "kittie_production_database",
        foreign_keys="kittie_production_database.updated_by_user_id",
        backref="updated_by_user",
        lazy=True
    )

    @staticmethod
    def get_auth_level(email):
        if email == 'hello@kittieproductions.co.uk':
            return 1
        elif '@kittieproductions.co.uk' in email:
            return 2
        else:
            return 3


class UserAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    actor_email_snapshot = db.Column(db.String(150))
    target_email_snapshot = db.Column(db.String(150))
    target_first_name_snapshot = db.Column(db.String(150))
    target_last_name_snapshot = db.Column(db.String(150))
    old_email = db.Column(db.String(150))
    new_email = db.Column(db.String(150))
    old_first_name = db.Column(db.String(150))
    new_first_name = db.Column(db.String(150))
    old_last_name = db.Column(db.String(150))
    new_last_name = db.Column(db.String(150))
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)


class kittie_production_database(db.Model):
    """
    Class defining the model for the Production database.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    dist_format = db.Column(db.String(150))
    length = db.Column(db.String(150))
    genre = db.Column(db.String(150))
    language = db.Column(db.String(150))
    setting = db.Column(db.String(150))
    est_budget = db.Column(db.String(150))
    cover_file_path = db.Column(db.String(255))
    one_sheet_file_path = db.Column(db.String(255))
    two_sheet_file_path = db.Column(db.String(255))
    pitch_deck_file_path = db.Column(db.String(255))
    budget_file_path = db.Column(db.String(255))
    treatment_file_path = db.Column(db.String(255))
    script_file_path = db.Column(db.String(255))
    cover_file_version = db.Column(db.Integer, nullable=True)
    one_sheet_file_version = db.Column(db.Integer, nullable=True)
    two_sheet_file_version = db.Column(db.Integer, nullable=True)
    pitch_deck_file_version = db.Column(db.Integer, nullable=True)
    budget_file_version = db.Column(db.Integer, nullable=True)
    treatment_file_version = db.Column(db.Integer, nullable=True)
    script_file_version = db.Column(db.Integer, nullable=True)
    url = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    updated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    production_permissions = db.relationship(
        "Permission",
        backref="kittie_production_database",
        cascade="all, delete",
        lazy=True
    )

    file_audit_logs = db.relationship(
        "FileAuditLog",
        backref="production",
        lazy=True,
        passive_deletes=True
    )

    file_access_logs = db.relationship(
        "FileAccessLog",
        backref="production",
        lazy=True,
        passive_deletes=True
    )

    permission_audit_logs = db.relationship(
        "PermissionAuditLog",
        backref="production",
        lazy=True,
        passive_deletes=True
    )

    production_audit_logs = db.relationship(
        "ProductionAuditLog",
        backref="production_record",
        lazy=True,
        passive_deletes=True
    )


class ProductionAuditLog(db.Model):
    """
    Full history of production record changes.
    Records who added/updated/removed a production, what changed, and when.
    """
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    actor_email_snapshot = db.Column(db.String(150))
    production_title_snapshot = db.Column(db.String(150))
    changed_fields = db.Column(db.Text)
    old_title = db.Column(db.String(150))
    new_title = db.Column(db.String(150))
    old_dist_format = db.Column(db.String(150))
    new_dist_format = db.Column(db.String(150))
    old_length = db.Column(db.String(150))
    new_length = db.Column(db.String(150))
    old_genre = db.Column(db.String(150))
    new_genre = db.Column(db.String(150))
    old_language = db.Column(db.String(150))
    new_language = db.Column(db.String(150))
    old_setting = db.Column(db.String(150))
    new_setting = db.Column(db.String(150))
    old_est_budget = db.Column(db.String(150))
    new_est_budget = db.Column(db.String(150))
    old_url = db.Column(db.String(150))
    new_url = db.Column(db.String(150))
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    production_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='SET NULL'), nullable=True)


class Permission(db.Model):
    """
    Class defining the model for live permissions.
    This stores the current access state only.
    """
    id = db.Column(db.Integer, primary_key=True)
    can_view = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    kittie_production_database_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='SET NULL'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint(
            'user_id',
            'kittie_production_database_id',
            name='uq_permission_user_production'
        ),
    )


class PermissionAuditLog(db.Model):
    """
    Full history of permission changes.
    Records who granted/removed access, for which user, on which production, and when.
    """
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    admin_email_snapshot = db.Column(db.String(150))
    target_email_snapshot = db.Column(db.String(150))
    production_title_snapshot = db.Column(db.String(150))
    admin_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    kittie_production_database_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='SET NULL'), nullable=True)


class FileAuditLog(db.Model):
    """
    Full history of file lifecycle changes.
    Records who added/replaced/removed a file, on which production, and when.
    """
    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    old_filename = db.Column(db.String(255))
    new_filename = db.Column(db.String(255))
    file_hash = db.Column(db.String(64))
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    actor_email_snapshot = db.Column(db.String(150))
    production_title_snapshot = db.Column(db.String(150))
    production_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='SET NULL'), nullable=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)


class FileAccessLog(db.Model):
    """
    Full history of file access.
    Records who viewed/downloaded a file, on which production, and when.
    """
    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_version = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.Text)
    watermark_lines = db.Column(db.String(500))
    watermark_token = db.Column(db.String(100))
    user_email_snapshot = db.Column(db.String(150))
    production_title_snapshot = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    production_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='SET NULL'), nullable=True)