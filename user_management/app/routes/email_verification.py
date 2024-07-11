from flask import Blueprint, render_template
from .. import db
from ..models import EmailVerificationToken, User


email_verificatoin_bp = Blueprint('verify-email', __name__)

@email_verificatoin_bp.route('/verify-email/<token>')
def verify_email(token):
    verification_token = EmailVerificationToken.query.filter_by(token=token).first_or_404()
    user = User.query.get(verification_token.user_id)
    user.email_verified = True
    db.session.commit()
    return render_template('email_verified.html')