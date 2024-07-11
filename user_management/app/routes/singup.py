from flask import Blueprint, request, jsonify
from .. import db, bcrypt
from ..models import User, Allowed_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
	data = request.get_json()
	email = data.get('email')
	name = data.get('name')
	password = data.get('password')

	if not email or not name or not password:
		return jsonify({'success': False, 'message': 'All fields are required'}), 400
	
	existing_user = User.query.filter_by(email=email).first()
	if existing_user:
		return jsonify({'success': False, 'message': 'User with this email address already exists'}), 400
	
	allowed_user = Allowed_user.query.filter_by(email=email).first()
	if not allowed_user:
		return jsonify({'success': False, 'message': 'This email is not allowed to sign up'}), 400

	hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

	new_user = User(email=email, name=name, password=hashed_password)
	try:
		db.session.add(new_user)
		db.session.commit()
	except Exception as e:
		print(f"Error adding user to the database: {e}")
		return jsonify({'success': False, 'message': 'Unexpected error occurred'}), 500

	return jsonify({'success': True, 'message': 'User registered successfully'}), 201