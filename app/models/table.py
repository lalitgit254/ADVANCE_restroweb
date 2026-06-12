from datetime import datetime, timezone
from app.extensions import db
import secrets


class Table(db.Model):
    __tablename__ = 'tables'

    id = db.Column(db.Integer, primary_key=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    table_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    table_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available', index=True)
    qr_code = db.Column(db.String(100), unique=True)
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bookings = db.relationship('Booking', backref='table', lazy='dynamic')

    TABLE_TYPES = ['2_seater', '4_seater', '6_seater', '8_seater']
    STATUSES = ['available', 'reserved', 'occupied']

    def generate_qr_code(self):
        self.qr_code = secrets.token_urlsafe(16)
        return self.qr_code

    def to_dict(self):
        return {
            'id': self.id,
            'branch_id': self.branch_id,
            'table_number': self.table_number,
            'capacity': self.capacity,
            'table_type': self.table_type,
            'status': self.status,
            'qr_code': self.qr_code,
            'location': self.location,
            'is_active': self.is_active,
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False, index=True)
    booking_time = db.Column(db.Time, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    special_requests = db.Column(db.Text)
    qr_code = db.Column(db.String(100), unique=True)
    confirmation_code = db.Column(db.String(20), unique=True)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    branch = db.relationship('Branch', backref='bookings')

    STATUSES = ['pending', 'confirmed', 'cancelled', 'completed', 'expired', 'no_show']

    def generate_codes(self):
        self.qr_code = secrets.token_urlsafe(16)
        self.confirmation_code = secrets.token_hex(4).upper()

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'table_id': self.table_id,
            'branch_id': self.branch_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'booking_time': self.booking_time.isoformat() if self.booking_time else None,
            'guests': self.guests,
            'status': self.status,
            'special_requests': self.special_requests,
            'confirmation_code': self.confirmation_code,
            'table': self.table.to_dict() if self.table else None,
        }


class WaitingList(db.Model):
    __tablename__ = 'waiting_list'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    preferred_table_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='waiting')
    position = db.Column(db.Integer)
    notified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship('User', backref='waiting_list_entries')
    branch = db.relationship('Branch', backref='waiting_list')
