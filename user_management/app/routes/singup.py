from flask import Blueprint, request, jsonify
from .. import db, bcrypt
from ..models import User, Allowed_user, EmailVerificationToken
import uuid
import boto3
import re

auth_bp = Blueprint('auth', __name__)

def send_verification_email(user, token):
    ses_client = boto3.client('ses', region_name='eu-central-1')
    verification_link = f"http://localhost:5000/verify_email/{token}"
    subject = "Verify your email address"
    body_text = f"""
    Hi {user.name},

    Please click the link below to verify your email address:

    {verification_link}

    If you did not request this, please ignore this email.

    Thank you,
    Your FOODBOT team
    """
    body_html = f"""
    <html>
    <head></head>
    <body>
        <p>Hi {user.name},</p>
        <p>Please click the link below to verify your email address:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Thank you,<br>Your FOODBOT team</p>
    </body>
    </html>
    """
    try:
        response = ses_client.send_email(
        Source='krus.frantisek@gmail.com',
        Destination={
            'ToAddresses': [user.email]
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                },
                'Html': {
                    'Data': body_html,
                    'Charset': 'UTF-8'
                }
            }
        }
    )   
        print(response)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email').lower()
    name = data.get('name')
    password = data.get('password')

    email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

    if not email or not name or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if not email_regex.match(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'User with this email address already exists'}), 400

    if not Allowed_user.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'This email is not allowed to sign up'}), 400
    
    if len(password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long'}), 400

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