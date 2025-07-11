import os
from . import db, DB_NAME, mail
from flask_mail import Message
from flask import current_app, render_template, session, abort
import secrets
import subprocess


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return session['_csrf_token']


def create_database(app):
    if not os.path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')


def generate_secure_token():
    return secrets.token_urlsafe(32)


def send_welcome_email(email, token, first_name):
    reset_url = f"https://www.kittieproductions.co.uk/update_password/{token}"
    msg = Message(
        subject="Welcome to Kittie Productions",
        recipients=[email],
        body=f"""
        
        Hi {first_name},
        
        Thank you for your interest in Kittie Productions.
        
        Please click the following link to set a password and view our upcoming productions:
        
        {reset_url}
        
        Once logged in, you will be directed to Kittie's latest projects.

        Kind regards,

        Kittie Productions
        www.kittieproductions.co.uk
        Content creation for Film and TV
                
        """
    )
    mail.send(msg)


def send_reset_email(email, token):
    reset_url = f"https://www.kittieproductions.co.uk/update_password/{token}"
    msg = Message(
        subject="Kittie Productions Password Reset",
        recipients=[email],
        body=f"""
        
        Hi there,

        Click the following link to reset your Kittie Productions password:

        {reset_url}

        You are receiving this message because a request was made using this email address.
        If you did not make the request, please ignore this message. No personal data has been compromised.

        Kind regards,

        Kittie Productions
        www.kittieproductions.co.uk
        Content creation for Film and TV
                
        """
    )
    mail.send(msg)