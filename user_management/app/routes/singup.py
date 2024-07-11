from flask import Blueprint, request, jsonify
from .. import db, bcrypt
from ..models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
	data = request.get_json()
	email = data.get('email')
	password = data.get('password')

	if not email or not password:
		return jsonify({'success': False, 'message': 'All fields are required'}), 400

	hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

	new_user = User(email=email, password=hashed_password)
	db.session.add(new_user)
	db.session.commit()

	return jsonify({'success': True, 'message': 'User registered successfully'}), 201