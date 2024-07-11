from flask import Blueprint, render_template

signup_page_bp = Blueprint('signup_page', __name__)

@signup_page_bp.route('/signup_page', methods=['GET'])
def signup_page():
    return render_template('signup.html')