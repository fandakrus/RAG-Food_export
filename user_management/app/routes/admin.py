from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
import bcrypt
from ..models import User
from .. import login_manager

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')) and user.role == "admin":
            login_user(user)
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid email or password')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
def admin_users():
    # Logic to fetch and display users
    return render_template('admin/users.html')