from datetime import datetime, timezone
from app.extensions import db


class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open', index=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime)

    user = db.relationship('User', foreign_keys=[user_id], backref='support_tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    messages = db.relationship('SupportMessage', backref='ticket', lazy='dynamic',
                               cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'messages': [m.to_dict() for m in self.messages],
        }


class SupportMessage(db.Model):
    __tablename__ = 'support_messages'

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    attachments = db.Column(db.JSON)
    is_staff_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', backref='support_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'message': self.message,
            'is_staff_reply': self.is_staff_reply,
            'sender': self.sender.to_dict() if self.sender else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FAQ(db.Model):
    __tablename__ = 'faqs'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='faqs')
