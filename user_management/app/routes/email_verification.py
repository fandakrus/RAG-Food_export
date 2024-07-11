from flask import Blueprint, render_template
from .. import db
from ..models import EmailVerificationToken, User


email_verification_bp = Blueprint('verify_email', __name__)

@email_verification_bp.route('/verify_email/<token>')
def verify_email(token):
    verification_token = EmailVerificationToken.query.filter_by(token=token).first()
    
    if not verification_token:
        return render_template('email_cannot_verify.html')
    
    user = User.query.get(verification_token.user_id)

    try:
        user.email_verified = True
        db.session.commit()
        return render_template('email_verified.html')
    except Exception as e:
        print(f"Error verifying email: {e}")
        return render_template('email_cannot_verify.html')