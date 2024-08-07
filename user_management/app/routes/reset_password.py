from flask import Blueprint, render_template, request, jsonify
from .. import db, bcrypt
from ..models import User, PasswordChangeToken

reset_password_bp = Blueprint('reset_password', __name__)

def verify_token(token):
    password_change_token = PasswordChangeToken.query.filter_by(token=token).first()

    if not password_change_token:
        return None

    user = User.query.get(password_change_token.user_id)

    return user

def remove_token(token):
    password_change_token = PasswordChangeToken.query.filter_by(token=token).first()

    if not password_change_token:
        return None

    try:
        db.session.delete(password_change_token)
        db.session.commit()
    except Exception as e:
        print(f"Error removing token: {e}")
        return None
    return True

@reset_password_bp.route('/reset_password_page/<token>', methods=['GET'])
def reset_password_page(token):
    user = verify_token(token)
    if not user:
        return render_template('reset_password_invalid_token.html')
    return render_template('reset_password.html', token=token)

@reset_password_bp.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    password = data.get('password')

    user = verify_token(token)
    if not user:
        return jsonify({'error': False, 'message': 'Invalid token'}), 400

    if len(password) < 8:
        return jsonify({'error': False, 'message': 'Password must be at least 8 characters long'}), 400

    try:
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
    except Exception as e:
        print(f"Error resetting password: {e}")
        return jsonify({'error': False, 'message': 'Unexpected error occurred'}), 500
    remove_token(token)
    return jsonify({'success': True, 'message': 'Password reset successfully'}), 200

@reset_password_bp.route('/password_reset_success', methods=['GET'])
def password_reset_success():
    return render_template('reset_password_success.html')

