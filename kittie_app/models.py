from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import event, ARRAY
import secrets
import subprocess
import hashlib
import json


class User(db.Model, UserMixin):
    """
    Class function defining the model for the User database
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150), nullable=False)
    last_name = db.Column(db.String(150), nullable=False)
    auth_level = db.Column(db.Integer, nullable=False)
    password_reset_token = db.Column(db.String(150), unique=True, nullable=True)
    password_updated = db.Column(db.Boolean, default=False)
    user_permissions = db.relationship("Permission", backref="user", cascade="all, delete", lazy=True)
 

    @staticmethod
    def get_auth_level(email):
        if email == 'hello@kittieproductions.co.uk':
            return 1
        elif '@kittieproductions.co.uk' in email:
            return 2
        else:
            return 3


class kittie_production_database(db.Model):
    """
    Class function defining the model for the Production database
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), unique=True, nullable=False)
    dist_format = db.Column(db.String(150))
    length = db.Column(db.String(150))
    genre = db.Column(db.String(150))
    language = db.Column(db.String(150))
    setting = db.Column(db.String(150))
    est_budget = db.Column(db.String(150))
    cover_file_path = db.Column(db.String(150))
    one_sheet_file_path = db.Column(db.String(150))
    pack_file_path = db.Column(db.String(150))
    budget_file_path = db.Column(db.String(150))
    treatment_file_path = db.Column(db.String(150))
    script_file_path = db.Column(db.String(150))
    url = db.Column(db.String(150), nullable=False)
    production_permissions = db.relationship("Permission", backref="kittie_production_database", cascade="all, delete", lazy=True)


class Permission(db.Model):
    """
    Class function defining the model for permissions
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    kittie_production_database_id = db.Column(db.Integer, db.ForeignKey('kittie_production_database.id', ondelete='CASCADE'), nullable=False)
    can_view = db.Column(db.Boolean, default=True)  # True if the user can view the record, False otherwise