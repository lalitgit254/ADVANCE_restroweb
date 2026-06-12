from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db, limiter
from app.services.auth_service import AuthService
from app.utils.helpers import get_dashboard_url, validate_email

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def login():
    if current_user.is_authenticated:
        return redirect(url_for(get_dashboard_url(current_user.role)))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        try:
            user = AuthService.login(email, password, remember=bool(remember))

            if user.two_factor_enabled:
                session['pending_2fa_user_id'] = user.id
                logout_user()
                return redirect(url_for('auth.verify_2fa'))

            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for(get_dashboard_url(user.role)))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('customer.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        referral_code = request.form.get('referral_code', '').strip()

        if not validate_email(email):
            flash('Invalid email address', 'danger')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
        elif password != confirm:
            flash('Passwords do not match', 'danger')
        else:
            try:
                AuthService.register(email, password, first_name, last_name, phone, referral_code)
                flash('Registration successful! Please check your email to verify.', 'success')
                return redirect(url_for('auth.login'))
            except ValueError as e:
                flash(str(e), 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('3 per minute')
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        AuthService.forgot_password(email)
        flash('If an account exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match', 'danger')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', 'danger')
        else:
            try:
                AuthService.reset_password(token, password)
                flash('Password reset successful!', 'success')
                return redirect(url_for('auth.login'))
            except ValueError as e:
                flash(str(e), 'danger')
    return render_template('auth/reset_password.html', token=token)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    try:
        AuthService.verify_email(token)
        flash('Email verified successfully!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/otp-login', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def otp_login():
    if request.method == 'POST':
        step = request.form.get('step', 'send')
        email = request.form.get('email', '').strip().lower()

        if step == 'send':
            AuthService.send_otp(email=email, purpose='login')
            flash('OTP sent to your email', 'info')
            return render_template('auth/otp_login.html', email=email, step='verify')
        else:
            otp = request.form.get('otp', '')
            try:
                user = AuthService.verify_otp(email, otp)
                flash('Login successful!', 'success')
                return redirect(url_for(get_dashboard_url(user.role)))
            except ValueError as e:
                flash(str(e), 'danger')
                return render_template('auth/otp_login.html', email=email, step='verify')

    return render_template('auth/otp_login.html', step='send')


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    user_id = session.get('pending_2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    from app.models.user import User
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        token = request.form.get('token', '')
        if AuthService.verify_2fa(user, token):
            session.pop('pending_2fa_user_id', None)
            login_user(user)
            flash('2FA verified!', 'success')
            return redirect(url_for(get_dashboard_url(user.role)))
        flash('Invalid 2FA code', 'danger')

    return render_template('auth/verify_2fa.html')


@auth_bp.route('/google')
def google_login():
    flash('Configure Google OAuth credentials in .env to enable Google login.', 'info')
    return redirect(url_for('auth.login'))
