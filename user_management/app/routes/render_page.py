from flask import Blueprint, render_template

page_bp = Blueprint('signup_page', __name__)

@page_bp.route('/signup_page', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@page_bp.route('/email_verify_page', methods=['GET'])
def email_verify_page():
    return render_template('email_verify.html')