from datetime import datetime, timezone
from app.extensions import db


class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price_monthly = db.Column(db.Numeric(10, 2), nullable=False)
    price_yearly = db.Column(db.Numeric(10, 2))
    max_branches = db.Column(db.Integer, default=1)
    max_staff = db.Column(db.Integer, default=10)
    features = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Restaurant(db.Model):
    __tablename__ = 'restaurants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    logo_url = db.Column(db.String(500))
    banner_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    opening_hours = db.Column(db.JSON)
    social_links = db.Column(db.JSON)
    gst_number = db.Column(db.String(20))
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    subscription_expires = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    subscription_plan = db.relationship('SubscriptionPlan', backref='restaurants')
    branches = db.relationship('Branch', backref='restaurant', lazy='dynamic')
    categories = db.relationship('Category', backref='restaurant', lazy='dynamic')
    food_items = db.relationship('FoodItem', backref='restaurant', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'logo_url': self.logo_url,
            'banner_url': self.banner_url,
            'description': self.description,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'opening_hours': self.opening_hours,
            'social_links': self.social_links,
            'gst_number': self.gst_number,
            'is_active': self.is_active,
        }


class Branch(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    tables = db.relationship('Table', backref='branch', lazy='dynamic')
    orders = db.relationship('Order', backref='branch', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'restaurant_id': self.restaurant_id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'is_active': self.is_active,
        }
