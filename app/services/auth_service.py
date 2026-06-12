import secrets
import pyotp
from datetime import datetime, timezone, timedelta
from flask import current_app
from flask_login import login_user
from app.extensions import db
from app.models.user import User, LoginActivity, OTPVerification
from app.services.email_service import EmailService
from app.services.loyalty_service import LoyaltyService
from app.utils.helpers import generate_otp, generate_referral_code, get_client_ip


class AuthService:
    @staticmethod
    def register(email, password, first_name, last_name, phone=None, referral_code=None):
        if User.query.filter_by(email=email).first():
            raise ValueError('Email already registered')

        if phone and User.query.filter_by(phone=phone).first():
            raise ValueError('Phone number already registered')

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='customer',
            referral_code=generate_referral_code(),
        )
        user.set_password(password)

        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                user.referred_by = referrer.id

        db.session.add(user)
        db.session.flush()

        LoyaltyService.get_or_create(user.id)

        if referral_code and user.referred_by:
            LoyaltyService.referral_reward(user.referred_by, user.id)

        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        db.session.commit()

        EmailService.send_verification_email(user, token)
        return user

    @staticmethod
    def login(email, password, remember=False):
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            AuthService._log_activity(user.id if user else None, 'password', False)
            raise ValueError('Invalid email or password')

        if not user.is_active:
            raise ValueError('Account is deactivated')

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user, remember=remember)
        AuthService._log_activity(user.id, 'password', True)
        return user

    @staticmethod
    def send_otp(email=None, phone=None, purpose='login'):
        otp = generate_otp()
        expires = datetime.now(timezone.utc) + timedelta(minutes=10)

        user = None
        if email:
            user = User.query.filter_by(email=email).first()
        elif phone:
            user = User.query.filter_by(phone=phone).first()

        otp_record = OTPVerification(
            user_id=user.id if user else None,
            email=email,
            phone=phone,
            otp_code=otp,
            purpose=purpose,
            expires_at=expires,
        )
        db.session.add(otp_record)
        db.session.commit()

        if email:
            EmailService.send_otp_email(email, otp)

        return otp_record

    @staticmethod
    def verify_otp(email, otp_code, purpose='login'):
        record = OTPVerification.query.filter_by(
            email=email, otp_code=otp_code, purpose=purpose, is_used=False
        ).order_by(OTPVerification.created_at.desc()).first()

        if not record:
            raise ValueError('Invalid OTP')
        if record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError('OTP expired')

        record.is_used = True
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError('User not found')

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        login_user(user)
        AuthService._log_activity(user.id, 'otp', True)
        return user

    @staticmethod
    def setup_2fa(user):
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        db.session.commit()
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=user.email, issuer_name='RestaurantPro')

    @staticmethod
    def verify_2fa(user, token):
        if not user.two_factor_secret:
            return False
        totp = pyotp.TOTP(user.two_factor_secret)
        return totp.verify(token, valid_window=1)

    @staticmethod
    def forgot_password(email):
        user = User.query.filter_by(email=email).first()
        if not user:
            return True

        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        EmailService.send_password_reset(user, token)
        return True

    @staticmethod
    def reset_password(token, new_password):
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            raise ValueError('Invalid reset token')
        if user.reset_token_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError('Reset token expired')

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return user

    @staticmethod
    def verify_email(token):
        user = User.query.filter_by(reset_token=token).first()
        if not user:
            raise ValueError('Invalid verification token')
        if user.reset_token_expires and user.reset_token_expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise ValueError('Verification token expired')

        user.email_verified = True
        user.is_verified = True
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        return user

    @staticmethod
    def google_login(google_id, email, first_name, last_name, avatar_url=None):
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_id
            else:
                user = User(
                    email=email,
                    google_id=google_id,
                    first_name=first_name,
                    last_name=last_name,
                    avatar_url=avatar_url,
                    role='customer',
                    email_verified=True,
                    is_verified=True,
                    referral_code=generate_referral_code(),
                )
                db.session.add(user)
                db.session.flush()
                LoyaltyService.get_or_create(user.id)

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        login_user(user)
        AuthService._log_activity(user.id, 'google', True)
        return user

    @staticmethod
    def _log_activity(user_id, method, success):
        if not user_id:
            return
        activity = LoginActivity(
            user_id=user_id,
            ip_address=get_client_ip(),
            user_agent=None,
            login_method=method,
            success=success,
        )
        db.session.add(activity)
        db.session.commit()
