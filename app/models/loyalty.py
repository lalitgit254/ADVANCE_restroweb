from datetime import datetime, timezone
from app.extensions import db


class LoyaltyPoint(db.Model):
    __tablename__ = 'loyalty_points'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True)
    total_points = db.Column(db.Integer, default=0)
    lifetime_points = db.Column(db.Integer, default=0)
    membership_level = db.Column(db.String(20), default='silver')
    cashback_balance = db.Column(db.Numeric(10, 2), default=0)
    referral_count = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='loyalty_members')
    transactions = db.relationship('LoyaltyTransaction', backref='loyalty', lazy='dynamic')

    LEVELS = {'silver': 0, 'gold': 1000, 'platinum': 5000}

    def update_level(self):
        if self.lifetime_points >= self.LEVELS['platinum']:
            self.membership_level = 'platinum'
        elif self.lifetime_points >= self.LEVELS['gold']:
            self.membership_level = 'gold'
        else:
            self.membership_level = 'silver'

    def to_dict(self):
        return {
            'total_points': self.total_points,
            'lifetime_points': self.lifetime_points,
            'membership_level': self.membership_level,
            'cashback_balance': float(self.cashback_balance),
            'referral_count': self.referral_count,
        }


class LoyaltyTransaction(db.Model):
    __tablename__ = 'loyalty_transactions'

    id = db.Column(db.Integer, primary_key=True)
    loyalty_id = db.Column(db.Integer, db.ForeignKey('loyalty_points.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    points = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    order = db.relationship('Order', backref='loyalty_transactions')
