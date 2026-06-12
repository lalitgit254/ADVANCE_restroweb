from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='customer', index=True)
    avatar_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    google_id = db.Column(db.String(100), unique=True)
    language = db.Column(db.String(5), default='en')
    dark_mode = db.Column(db.Boolean, default=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    referral_code = db.Column(db.String(20), unique=True)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    birthday = db.Column(db.Date)
    anniversary = db.Column(db.Date)
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='users', foreign_keys=[restaurant_id])
    branch = db.relationship('Branch', backref='users', foreign_keys=[branch_id])
    staff_profile = db.relationship('Staff', backref='user', uselist=False)
    loyalty = db.relationship('LoyaltyPoint', backref='user', uselist=False)
    orders = db.relationship('Order', backref='customer', foreign_keys='Order.customer_id')
    bookings = db.relationship('Booking', backref='customer', foreign_keys='Booking.customer_id')
    reviews = db.relationship('Review', backref='user')
    cart = db.relationship('Cart', backref='user', uselist=False)

    ROLES = ['super_admin', 'admin', 'manager', 'chef', 'waiter', 'cashier', 'delivery_boy', 'customer']

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def has_role(self, *roles):
        return self.role in roles

    def can_access_admin(self):
        return self.role in ('super_admin', 'admin', 'manager')

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'avatar_url': self.avatar_url,
            'is_verified': self.is_verified,
            'language': self.language,
            'dark_mode': self.dark_mode,
            'restaurant_id': self.restaurant_id,
            'branch_id': self.branch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        return data


class LoginActivity(db.Model):
    __tablename__ = 'login_activity'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    login_method = db.Column(db.String(30))
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='login_activities')


class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    otp_code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(30), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref='otp_verifications')
