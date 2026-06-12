from datetime import datetime, timezone
from app.extensions import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    razorpay_signature = db.Column(db.String(256))
    transaction_id = db.Column(db.String(100), unique=True)
    gst_amount = db.Column(db.Numeric(10, 2), default=0)
    invoice_number = db.Column(db.String(50), unique=True)
    refund_amount = db.Column(db.Numeric(10, 2), default=0)
    refund_reason = db.Column(db.Text)
    refunded_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship('User', backref='payments')

    METHODS = ['upi', 'credit_card', 'debit_card', 'net_banking', 'wallet', 'cash']
    STATUSES = ['pending', 'processing', 'completed', 'failed', 'refunded', 'partially_refunded']

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'invoice_number': self.invoice_number,
            'gst_amount': float(self.gst_amount) if self.gst_amount else 0,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
        }


class Coupon(db.Model):
    __tablename__ = 'coupons'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    discount_type = db.Column(db.String(20), nullable=False)
    discount_value = db.Column(db.Numeric(10, 2), nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2), default=0)
    max_discount = db.Column(db.Numeric(10, 2))
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='coupons')

    def is_valid(self, order_amount=0):
        now = datetime.now(timezone.utc)
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from.replace(tzinfo=timezone.utc):
            return False
        if self.valid_until and now > self.valid_until.replace(tzinfo=timezone.utc):
            return False
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        if float(order_amount) < float(self.min_order_amount):
            return False
        return True

    def calculate_discount(self, order_amount):
        if self.discount_type == 'percentage':
            discount = float(order_amount) * float(self.discount_value) / 100
            if self.max_discount:
                discount = min(discount, float(self.max_discount))
        else:
            discount = float(self.discount_value)
        return min(discount, float(order_amount))
