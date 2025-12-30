"""
Admin routes: user management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from dogs_app.models import User
from dogs_app import db

admin_bp = Blueprint('admin', __name__)

# User roles
USER_ROLES = ['admin', 'doctor', 'viewer']


@admin_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Register a new user (admin only)."""
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'viewer')
        full_name = request.form.get('full_name')
        email = request.form.get('email')

        if not username or not password:
            flash('Username and password are required')
            return render_template('register.html', roles=USER_ROLES)

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html', roles=USER_ROLES)

        if role not in USER_ROLES:
            flash('Invalid role')
            return render_template('register.html', roles=USER_ROLES)

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            full_name=full_name,
            email=email,
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        flash('User registered successfully')
        return redirect(url_for('admin.manage_users'))

    return render_template('register.html', roles=USER_ROLES)


@admin_bp.route('/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    """Manage users (admin only)."""
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')

        if action == 'edit':
            user = User.query.get_or_404(user_id)
            user.username = request.form.get('username')
            user.role = request.form.get('role')
            user.full_name = request.form.get('full_name')
            user.email = request.form.get('email')
            user.is_active = request.form.get('is_active') == 'on'

            # Prevent admin from deactivating themselves
            if int(user_id) == current_user.id and not user.is_active:
                flash('Cannot deactivate your own account')
                user.is_active = True

            db.session.commit()
            flash('User updated successfully')

        elif action == 'delete':
            if int(user_id) == current_user.id:
                flash('Cannot delete your own account')
            else:
                user = User.query.get_or_404(user_id)
                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully')

        elif action == 'reset_password':
            new_password = request.form.get('new_password')
            if new_password:
                user = User.query.get_or_404(user_id)
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                flash(f'Password reset for {user.username}')
            else:
                flash('No password provided')

    users = User.query.order_by(User.username).all()
    return render_template('manage_users.html', users=users, roles=USER_ROLES)
