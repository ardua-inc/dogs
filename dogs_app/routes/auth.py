"""
Authentication routes: login, logout, password management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from dogs_app.models import User
from dogs_app import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dogs.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact an administrator.')
                return render_template('login.html')
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dogs.index'))
        flash('Invalid username or password')

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change."""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(current_user.password_hash, old_password):
            flash('Incorrect current password')
            return render_template('change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match')
            return render_template('change_password.html')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('change_password.html')

        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Password changed successfully')
        return redirect(url_for('dogs.index'))

    return render_template('change_password.html')
