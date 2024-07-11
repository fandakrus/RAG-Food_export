from flask import Blueprint, request, jsonify
from flask_mail import Message
from .. import db, mail, bcrypt
from ..models import User, Allowed_user, EmailVerificationToken
import uuid

auth_bp = Blueprint('auth', __name__)

def send_verification_email(user, token):
    msg = Message('Email Verification', sender='noreply@foodbot.com', recipients=[user.email])
    verification_link = f"http://localhost:5000/verify_email/{token}"
    msg.body = f"""
    Hi {user.name},

    Please click the link below to verify your email address:

    {verification_link}

    If you did not request this, please ignore this email.

    Thank you,
    Your FOODBOT team
    """
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')

    if not email or not name or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'User with this email address already exists'}), 400

    if not Allowed_user.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'This email is not allowed to sign up'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email=email, name=name, password=hashed_password)

    if not add_user_to_db(new_user):
        return jsonify({'success': False, 'message': 'Unexpected error occurred'}), 500

    token = str(uuid.uuid4())
    verification_token = EmailVerificationToken(user_id=new_user.id, token=token)

    if not add_verification_token_to_db(verification_token):
        return jsonify({'success': False, 'message': 'Unexpected error occurred'}), 500

    if not send_verification_email(new_user, token):
        return jsonify({'success': False, 'message': 'Failed to send verification email'}), 500
    
    return jsonify({'success': True, 'message': 'User registered successfully. Please check your email to verify your account.'}), 201

def add_user_to_db(user):
    try:
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding user to the database: {e}")
        return False

def add_verification_token_to_db(token):
    try:
        db.session.add(token)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding verification token to the database: {e}")
        return False