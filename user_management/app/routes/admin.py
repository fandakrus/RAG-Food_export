import csv
import pandas as pd
from io import StringIO, BytesIO
import re
import boto3
import uuid
from itertools import zip_longest
from flask import Blueprint, render_template, redirect, url_for, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User, Allowed_user, PasswordChangeToken
from .. import login_manager, db, bcrypt

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


class UserEmail:
    def __init__(self, email, first_name=None, last_name=None, organization=None):
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.organization = organization

    def generate_greating(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}" + (f", {self.organization}" if self.organization else "")
        if self.first_name:
            return f"{self.first_name}" + (f", {self.organization}" if self.organization else "")
        if self.last_name:
            return f"{self.last_name}" + (f", {self.organization}" if self.organization else "")
        return "User"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form['email']
            password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password.encode('utf-8')) and user.role == "admin":
            login_user(user)
            return jsonify({'message': 'Login successful', 'redirect': url_for('admin.admin_dashboard')}), 200
        else:
            return jsonify({'message': 'Invalid email or password'}), 401
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def admin_dashboard():
    user_count = User.query.count()
    return render_template('admin/dashboard.html', user_count=user_count)

@admin_bp.route('/users')
def admin_users():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if search_query:
        pagination = User.query.filter(User.email.ilike(f'%{search_query}%')).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)

    users = pagination.items
    return render_template('admin/users.html', users=users, pagination=pagination, search_query=search_query)

def add_user_to_db(user):
    try:
        db.session.add(user)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding user to the database: {e}")
        return False

@admin_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON data'}), 400
        email = data.get('email').lower()
        name = data.get('name')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        role = data.get('role')
        email_verified = data.get('email_verified', False)
        email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

        if not email or not name or not password or not confirm_password:
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
        
        if not email_regex.match(email):
            return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': 'User with this email address already exists'}), 400
        
        if len(password) < 8:
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters long'}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, name=name, password=hashed_password, role=role, email_verified=email_verified)

        if not add_user_to_db(new_user):
            return jsonify({'success': False, 'message': 'Unexpected error occurred'}), 500
        
        if not Allowed_user.query.filter_by(email=email).first():
            allowed_user = Allowed_user(email=email)
            try:
                db.session.add(allowed_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': str(e)}), 500
        
        return jsonify({'status': 'success', 'message': 'User added successfully'}), 201
    return render_template('admin/add_user.html')

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    allowed_address = Allowed_user.query.filter_by(email = user.email).first()
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON data'}), 400
        if user.id == current_user.id and data.get('role') != 'admin':
            return jsonify({'status': 'error', 'message': 'You cannot demote yourself!'}), 400
        user.email = data.get('email')
        user.name = data.get('name')
        user.role = data.get('role')
        user.email_verified = data.get('email_verified', False)
        if allowed_address:
            allowed_address.email = data.get('email')
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'status': 'error', 'message': 'You cannot delete yourself!'}), 400
    else:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    
@admin_bp.route('/change_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'Invalid JSON data'}), 400
        
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if new_password != confirm_password:
            return jsonify({'status': 'error', 'message': 'Passwords do not match!'}), 400
        
        user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Password changed successfully'}), 200
    
    return render_template('admin/change_password.html', user=user)

@admin_bp.route('/allowed_addresses')
@login_required
def allowed_addresses():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    if search_query:
        pagination = Allowed_user.query.filter(User.email.ilike(f'%{search_query}%')).paginate(page=page, per_page=per_page, error_out=False)
    else:
        pagination = Allowed_user.query.paginate(page=page, per_page=per_page, error_out=False)

    users = pagination.items
    return render_template('admin/allowed_addresses.html', users=users, pagination=pagination, search_query=search_query)

@admin_bp.route('/delete_address/<int:user_id>', methods=['POST'])
@login_required
def delete_address(user_id):
    allowed_user = Allowed_user.query.get_or_404(user_id)
    try:
        if allowed_user.email == current_user.email:
            return jsonify({'success': False, 'message': 'You cannot delete yourself.'}), 403
        db.session.delete(allowed_user)

        user = User.query.filter_by(email=allowed_user.email).first()
        if user:
            db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Address deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
def send_signup_email(email: UserEmail):
    ses_client = boto3.client('ses', region_name='ap-southeast-1')
    signup_url = f"https://foodprobot.com/signup_page?email={email.email}"
    subject = "Sign Up for Foodpro chatbot App"
    greating = email.generate_greating()
    body_text = f"""
    สวัสดีครับ คุณ {greating},
    ผม ดร.เจษฎา ทิพย์มณเฑียร หัวหน้าวิทยการ หลักสูตร FSPCA Preventive Controls for Human Food (PCQI for Human Food) หลักสูตร FSPCA Preventive Controls for Animal Food (PCQI for Animal Food) หลักสูตร FSPCA Foreign Supplier Verification Programs (FSVP) หลักสูตร FSPCA Intentional Adulteration Conducting Vulnerability Assessments (IAVA)   รวมทั้งวิทยากรและที่ปรึกษาเกี่ยวกับกฎหมายหมาย ระเบียบและการปฏิบัติการที่เป็นเลิศเหนือมาตรฐานเพื่อการส่งออกอาหารไป
    สหรัฐอเมริกา (ดูประวัติเพิ่มเติมได้ที่ https://beyondstandards.com/jedsada/ )  ผมส่งข้อความนี้มาเพื่อเชิญท่านเข้าใช้แอพพลิเคชั่น FOODPRO BOT 

    FOODPRO BOT เป็นแอพพลิเคชั่น ช่วยให้ท่านเหมือนมีที่ปรึกษาส่วนตัวให้คำแนะนำเรื่องกฎระเบียบเพื่อส่งออกอาหารไปอเมริกา แหล่งข้อมูลอ้างอิงส่วนใหญ่มาจากกฎหมาย ระเบียบและประกาศจากสำนักงานคณะกรรมการอาหารและยาสหรัฐอเมริกาซึ่งเป็นภาษาอังกฤษ ท่านสามารถตั้งคำถามเป็นภาษาไทยได้ แต่การตั้งคำถามที่มีความเฉพาะเจาะจงที่เป็นภาษาอังกฤษจะช่วยให้ท่านได้คำตอบที่ถูกต้องและรวดเร็วขึ้น

    เพื่อรักษาสิทธิการเข้าใช้แอพพลิเคชั่น แบบไม่มีค่าใช้จ่าย โปรดลงทะเบียน {signup_url} foodprobot ภายใน 31 สิงหาคม 2567 เวลา 24.00 น.
    ผมหวังว่า แอพพลิเคชั่น FOODPROBOT จะช่วยแนะนำข้อมูลที่เป็นประโยชน์ให้กับท่าน อย่างไรก็ตาม โปรดทราบว่าข้อมูลที่ได้รับจะเป็นอธิบายให้คำตอบเพื่อให้แนวคิดในการกำหนดแนวทางปฏิบัติได้ แต่อาจไม่ได้รับประกันความสมบูรณ์ของคำตอบ 100% ขึ้นอยู่กับรายละเอียดผลิตภัณฑ์และบริบททางธุรกิจเพิ่มเติม ท่านต้องดูรายละเอียดข้อกำหนดทางกฎหมายประกอบให้ชัดเจนหรือปรึกษาผู้เชี่ยวชาญเพิ่มเติมก่อนนำคำตอบไปใช้  ต้องการแนะนำ เสนอแนะติดต่อที่ ดร.เจษฎา ทิพย์มณเฑียร LINE ID:@jedsada 



    Dear {greating},

    I am Dr. Jedsada Tipmontian, Lead Instructor for FSPCA Preventive Controls for Human Food (PCQI for Human Food) Course, FSPCA Preventive Controls for Animal Food (PCQI for Animal Food) Course, FSPCA Foreign Supplier Verification Programs (FSVP), FSPCA and Intentional Adulteration Conducting Vulnerability Assessments (IAVA) under Food Safety Modernization Act (FSMA).  I am an Instructor and Consultant in the field of Regulatory Compliance and Operations Excellence Beyond Standards for Exporting Food to the U.S. (more information at https://beyondstandards.com/jedsada/ )

    I am sending this email inviting you to use the application "FOODPRO BOT".
    FOODPRO BOT is working as your personal consultant to achieve operations excellence with USFDA compliance. To be eligible for free, please register to start using FOODPRO BOT at {signup_url} by or before August 31, 2024.

    I hope this will be useful for your business. This application can give you ideas and guidelines however please be aware that results from FOODPRO BOT  cannot guarantee 100% completion depending on product characteristics and business contexts. You need to refer to concerned laws and regulations or consult with your regulation specialists when you need to apply the answer result in practice.

    If you have any suggestions please contact: Dr. Jedsada Tipmontian LINE:@jedsada 

    ขอขอบคุณและแสดงความนับถือ,
    ดร.เจษฎา ทิพย์มณเฑียร
    www.beyondstandards.com
    LINE:@jedsada
    """
    body_html = f"""
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>Sign Up for Foodpro chatbot App</title>
    </head>
    <body>
        <p>สวัสดีครับ คุณ {greating},</p>

        <p>ผม ดร.เจษฎา ทิพย์มณเฑียร หัวหน้าวิทยการ หลักสูตร FSPCA Preventive Controls for Human Food (PCQI for Human Food) หลักสูตร FSPCA Preventive Controls for Animal Food (PCQI for Animal Food) หลักสูตร FSPCA Foreign Supplier Verification Programs (FSVP) หลักสูตร FSPCA Intentional Adulteration Conducting Vulnerability Assessments (IAVA) รวมทั้งวิทยากรและที่ปรึกษาเกี่ยวกับกฎหมายหมาย ระเบียบและการปฏิบัติการที่เป็นเลิศเหนือมาตรฐานเพื่อการส่งออกอาหารไป สหรัฐอเมริกา (ดูประวัติเพิ่มเติมได้ที่ <a href="https://beyondstandards.com/jedsada/">https://beyondstandards.com/jedsada/</a>) ผมส่งข้อความนี้มาเพื่อเชิญท่านเข้าใช้แอพพลิเคชั่น FOODPRO BOT</p>

        <p>FOODPRO BOT เป็นแอพพลิเคชั่น ช่วยให้ท่านเหมือนมีที่ปรึกษาส่วนตัวให้คำแนะนำเรื่องกฎระเบียบเพื่อส่งออกอาหารไปอเมริกา แหล่งข้อมูลอ้างอิงส่วนใหญ่มาจากกฎหมาย ระเบียบและประกาศจากสำนักงานคณะกรรมการอาหารและยาสหรัฐอเมริกาซึ่งเป็นภาษาอังกฤษ ท่านสามารถตั้งคำถามเป็นภาษาไทยได้ แต่การตั้งคำถามที่มีความเฉพาะเจาะจงที่เป็นภาษาอังกฤษจะช่วยให้ท่านได้คำตอบที่ถูกต้องและรวดเร็วขึ้น</p>

        <p>เพื่อรักษาสิทธิการเข้าใช้แอพพลิเคชั่น แบบไม่มีค่าใช้จ่าย โปรดลงทะเบียน <a href="{signup_url}">{signup_url}</a> foodprobot ภายใน 31 สิงหาคม 2567 เวลา 24.00 น.</p>

        <p>ผมหวังว่า แอพพลิเคชั่น FOODPROBOT จะช่วยแนะนำข้อมูลที่เป็นประโยชน์ให้กับท่าน อย่างไรก็ตาม โปรดทราบว่าข้อมูลที่ได้รับจะเป็นอธิบายให้คำตอบเพื่อให้แนวคิดในการกำหนดแนวทางปฏิบัติได้ แต่อาจไม่ได้รับประกันความสมบูรณ์ของคำตอบ 100% ขึ้นอยู่กับรายละเอียดผลิตภัณฑ์และบริบททางธุรกิจเพิ่มเติม ท่านต้องดูรายละเอียดข้อกำหนดทางกฎหมายประกอบให้ชัดเจนหรือปรึกษาผู้เชี่ยวชาญเพิ่มเติมก่อนนำคำตอบไปใช้ ต้องการแนะนำ เสนอแนะติดต่อที่ ดร.เจษฎา ทิพย์มณเฑียร LINE ID:@jedsada</p>

        <br><br>

        <p>Dear {greating},</p>

        <p>I am Dr. Jedsada Tipmontian, Lead Instructor for FSPCA Preventive Controls for Human Food (PCQI for Human Food) Course, FSPCA Preventive Controls for Animal Food (PCQI for Animal Food) Course, FSPCA Foreign Supplier Verification Programs (FSVP), FSPCA and Intentional Adulteration Conducting Vulnerability Assessments (IAVA) under Food Safety Modernization Act (FSMA). I am an Instructor and Consultant in the field of Regulatory Compliance and Operations Excellence Beyond Standards for Exporting Food to the U.S. (more information at <a href="https://beyondstandards.com/jedsada/">https://beyondstandards.com/jedsada/</a>)</p>

        <p>I am sending this email inviting you to use the application "FOODPRO BOT". FOODPRO BOT is working as your personal consultant to achieve operations excellence with USFDA compliance. To be eligible for free, please register to start using FOODPRO BOT at <a href="{signup_url}">{signup_url}</a> by or before August 31, 2024.</p>

        <p>I hope this will be useful for your business. This application can give you ideas and guidelines however please be aware that results from FOODPRO BOT cannot guarantee 100% completion depending on product characteristics and business contexts. You need to refer to concerned laws and regulations or consult with your regulation specialists when you need to apply the answer result in practice.</p>

        <p>If you have any suggestions please contact: Dr. Jedsada Tipmontian LINE:@jedsada</p>

        <br><br>

        <p>ขอขอบคุณและแสดงความนับถือ,<br>
        ดร.เจษฎา ทิพย์มณเฑียร<br>
        <a href="http://www.beyondstandards.com">www.beyondstandards.com</a><br>
        LINE:@jedsada</p>
    </body>
    </html>
    """
    try:
        response = ses_client.send_email(
            Source='register@foodprobot.com',
            Destination={
                'ToAddresses': [email.email]
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
        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return None
    
@admin_bp.route('/add_address', methods=['GET', 'POST'])
@login_required
def add_address():
    if request.method == 'GET':
        return render_template('admin/add_address.html')

    if request.method == 'POST':
        user_emails = []

        # Check if a file is uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file.filename.endswith('.xlsx'):
                file_stream = BytesIO(file.stream.read())
                # Read Excel file
                df = pd.read_excel(file_stream)
                df.columns = df.columns.str.lower()
                try:
                    emails = df['email'].tolist()

                    if 'first name' in df.columns:
                        first_names = df['first name'].tolist()
                    if 'last name' in df.columns:
                        last_names = df['last name'].tolist()
                    if 'organization' in df.columns:
                        organizations = df['organization'].tolist()
                except KeyError:
                    return jsonify({'success': False, 'message': 'Excel file must have a column named "email"'}), 400
                for email, first_name, last_name, organization in zip_longest(emails, first_names, last_names, organizations, fillvalue=None):
                    user_emails.append(UserEmail(email, first_name, last_name, organization))

            elif file.filename.endswith('.csv'):
                # Read CSV file
                stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = csv.reader(stream)
                user_emails = [UserEmail(email.strip()) for row in csv_input for email in row]              
            else:
                # Read text file
                user_emails = [UserEmail(email.strip()) for email in re.split(r'[,\n]', file.stream.read().decode("UTF8"))]

        elif 'emails' in request.form:
            user_emails = [UserEmail(email.strip()) for email in re.split(r'[,\n]', request.form['emails'])]

        email_regex = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

        # Filter out invalid email addresses
        valid_emails = [user_email for user_email in user_emails if email_regex.match(user_email.email)]
        invalid_counter = 0
        invalid_addresses = []
        # Add emails to Allowed_user table
        for email in valid_emails:
            if not Allowed_user.query.filter_by(email=email.email).first():
                allowed_user = Allowed_user(email=email.email)
                db.session.add(allowed_user)
                if send_signup_email(email) is None:
                    invalid_counter += 1
                    invalid_addresses.append(email.email)

        try:
            db.session.commit()
            if invalid_counter > 0:
                return jsonify({'success': False, 'message': f"""Addresses added successfully. {invalid_counter} emails were not succesfully send to users. These are {[address for address in invalid_addresses]}"""}), 500
            return jsonify({'success': True, 'message': 'Addresses added successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
        
def send_password_reset_email(user, token):
    ses_client = boto3.client('ses', region_name='ap-southeast-1')
    verification_link = f"https://foodprobot.com/reset_password_page/{token}"
    subject = "Reset Your Password"
    body_text = f"""
    Hi {user.name},

    Please click the link below to reset your password:

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
        <p>Please click the link below to reset your password:</p>
        <p><a href="{verification_link}">{verification_link}</a></p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Thank you,<br>Your FOODBOT team</p>
    </body>
    </html>
    """
    try:
        response = ses_client.send_email(
        Source='noreply@foodprobot.com',
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

def add_password_reset_token_to_db(token):
    try:
        db.session.add(token)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error adding verification token to the database: {e}")
        return False

@admin_bp.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)
    token = str(uuid.uuid4())
    verification_token = PasswordChangeToken(user_id=user.id, token=token)

    if not add_password_reset_token_to_db(verification_token):
        return jsonify({'success': False, 'message': 'Unexpected error occurred'}), 500
    
    if not send_password_reset_email(user, token):
        return jsonify({'success': False, 'message': 'Failed to send password email'}), 500
    
    return jsonify({'success': True, 'message': 'Email with instructions send to the user'}), 201
