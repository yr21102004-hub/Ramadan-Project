from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import random
import string
from models import UserModel, SecurityLogModel
from models.user import User

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
user_model = UserModel()
security_model = SecurityLogModel()

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_sms_otp(phone, code):
    """
    Simulates sending an SMS/WhatsApp OTP.
    Logs the code for the admin to see and flash for the user.
    """
    # In a real scenario, this would call a WhatsApp/SMS API
    print(f"DEBUG: Sending OTP {code} to {phone}")
    security_model.create("OTP Sent", f"Code {code} sent to {phone}", severity="low")
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        
        user_data = user_model.get_by_username(username)
        user = User.get(username) if user_data else None
        
        if user_data and bcrypt.check_password_hash(user_data.get('password', ''), password):
            if user.two_factor_enabled:
                otp = generate_otp()
                session['2fa_user'] = username
                session['otp_code'] = otp
                # Send the code
                send_sms_otp(user_data.get('phone'), otp)
                flash('تم إرسال رمز التحقق إلى هاتفك')
                return redirect(url_for('auth.verify_2fa'))
            
            login_user(user)
            return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'web.index'))
        
        security_model.create("Failed Login", f"Attempt for username: {username}", severity="medium")
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')

    return render_template('login.html', captcha_q=None)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('web.index'))

@auth_bp.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if '2fa_user' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        username = session['2fa_user']
        user = User.get(username)
        
        # Check against session OTP first (SMS mode)
        stored_otp = session.get('otp_code')
        
        if code == stored_otp:
            login_user(user)
            session.pop('2fa_user', None)
            session.pop('otp_code', None)
            flash('تم تسجيل الدخول بنجاح')
            return redirect(url_for('admin.admin_dashboard' if user.role == 'admin' else 'web.index'))
        else:
            # Fallback for TOTP if needed, but user specifically asked for SMS
            flash('رمز التحقق غير صحيح')
            
    return render_template('verify_2fa.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        
        user_data = user_model.get_by_username(username)
        if user_data and user_data.get('phone') == phone:
            otp = generate_otp()
            session['reset_user'] = username
            session['otp_code'] = otp
            send_sms_otp(phone, otp)
            flash('تم إرسال كود التحقق بنجاح')
            return redirect(url_for('auth.verify_code'))
        else:
            flash('البيانات المدخلة غير صحيحة')
            
    return render_template('forgot_password.html')

@auth_bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    if 'reset_user' not in session:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        if code == session.get('otp_code'):
            return redirect(url_for('auth.reset_new_password'))
        else:
            flash('كود التحقق غير صحيح')
            
    return render_template('verify_code.html')

@auth_bp.route('/reset_new_password', methods=['GET', 'POST'])
def reset_new_password():
    if 'reset_user' not in session:
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        user_model.update(session['reset_user'], {'password': hashed})
        session.pop('reset_user', None)
        session.pop('otp_code', None)
        flash('تم تغيير كلمة المرور بنجاح')
        return redirect(url_for('auth.login'))
        
    return render_template('reset_new_password.html')
