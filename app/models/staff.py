from datetime import datetime, timezone
from app.extensions import db


class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    employee_id = db.Column(db.String(50), unique=True)
    designation = db.Column(db.String(100))
    salary = db.Column(db.Numeric(10, 2))
    join_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='staff_members')
    branch = db.relationship('Branch', backref='staff_members')
    attendance_records = db.relationship('Attendance', backref='staff', lazy='dynamic')
    payroll_records = db.relationship('Payroll', backref='staff', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'designation': self.designation,
            'salary': float(self.salary) if self.salary else None,
            'join_date': self.join_date.isoformat() if self.join_date else None,
            'is_active': self.is_active,
            'user': self.user.to_dict() if self.user else None,
        }


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    date = db.Column(db.Date, nullable=False, index=True)
    hours_worked = db.Column(db.Float)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Payroll(db.Model):
    __tablename__ = 'payroll'

    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    base_salary = db.Column(db.Numeric(10, 2), nullable=False)
    bonus = db.Column(db.Numeric(10, 2), default=0)
    deductions = db.Column(db.Numeric(10, 2), default=0)
    net_salary = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
