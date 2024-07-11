from flask import Blueprint, render_template

email_verify_page_bp = Blueprint('email_verify_page', __name__)

@email_verify_page_bp.route('/email_verify_page', methods=['GET'])
def email_verify_page():
    return render_template('email_verify.html')