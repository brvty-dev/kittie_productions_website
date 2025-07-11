from flask import Blueprint, render_template, request, flash, redirect, url_for, get_flashed_messages, current_app, make_response
from kittie_app.models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from kittie_app.utils import generate_secure_token, send_reset_email
from flask_login import login_user, login_required, logout_user, current_user
import secrets
import re
import logging
logging.basicConfig(level=logging.INFO)


auth = Blueprint('auth', __name__)


@auth.route('/adam', methods=['GET', 'POST'])
def adam():
    kittie_production = None
    auth_level = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')

        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*-?&£])[A-Za-z\d@$!%*-?&£]{8,}$"

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        if not re.match(email_pattern, email):
            flash('Invalid email address.', category='error')
        if not re.match(password_pattern, password):
            flash('Password must be at least 8 characters long and contain at least one number, one upper case letter, one lower case letter and one symbol from @$!%*-?&£', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(last_name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        else:
            # Determine auth_level based on email conditions
            auth_level = User.get_auth_level(email)

        # Create the first user
        new_user = User(
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            first_name=first_name,
            last_name=last_name,
            auth_level=auth_level
        )

        # Add the first user to the database
        db.session.add(new_user)
        db.session.commit()

        flash('First user added successfully!', category='success')
        return redirect(url_for('auth.login', user=current_user, kittie_production=kittie_production))

    return render_template('adam.html', user=current_user, kittie_production=kittie_production)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    kittie_production = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.password != None:
            # Check if the provided password matches the hashed password in the database
                if check_password_hash(user.password, password):
                    flash("You've been logged in successfully!", category='success')
                    login_user(user, remember=True)
                    if current_user.is_authenticated:
                        return redirect(url_for('views.kittie_productions', user=current_user, kittie_production=kittie_production))
                else:
                    flash('Incorrect password, try again.', category='error')
            else:
                flash('You need to set your password first.', category='error')
        else:
            flash('User not found.', category='error')
    return render_template("login.html", user=current_user, kittie_production=kittie_production)

 
@auth.route('/logout')
@login_required
def logout():
    kittie_production = None
    logout_user()
    return redirect(url_for('views.index', user=current_user, kittie_production=kittie_production))


@auth.route('/forgotten_password', methods=['GET', 'POST'])
def forgotten_password():
    kittie_production = None
    if request.method == 'POST':
        email = request.form['email']

        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_secure_token()
            user.password_reset_token = token
            db.session.commit()

            send_reset_email(email, token)

            flash('Password reset instructions have been sent to your email.', category='success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email address not recognised.', category='error')
            return redirect('auth.forgotten_password')
    return render_template("forgotten_password.html", user=current_user, kittie_production=kittie_production)


@auth.route('/update_password', methods=['GET', 'POST'])
def update_password():
    kittie_production = None
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Regular expression to enforce password complexity
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*-?&£])[A-Za-z\d@$!%*-?&£]{8,}$"
        
        if password != confirm_password:
            flash('Passwords don\'t match.', category='error')
        if not re.match(password_pattern, password):
            flash('Password must be at least 8 characters long and contain at least one number, one upper case letter, one lower case letter and one symbol from @$!%*-?&£', category='error')
        else:
            token = request.view_args.get('token')
            user = User.query.filter_by(password_reset_token=token).first()
            if user:
                # Update the user's password
                user.password = generate_password_hash(password, method='pbkdf2:sha256')
                user.password_reset_token = None
                user.password_updated = True

                # Commit the changes to the database
                db.session.commit()

                # Log in the user
                login_user(user, remember=True)

                # Redirect to a page after successful password update
                return redirect(url_for('views.kittie_productions', user=current_user.id))
            else:
                flash('Invalid or expired token.', category='error')
        
    return render_template("update_password.html", user=current_user, kittie_production=kittie_production)