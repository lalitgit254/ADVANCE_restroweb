from datetime import datetime, timezone
from app.extensions import db


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, unique=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    food_rating = db.Column(db.Integer)
    service_rating = db.Column(db.Integer)
    ambience_rating = db.Column(db.Integer)
    cleanliness_rating = db.Column(db.Integer)
    overall_rating = db.Column(db.Float)
    review_text = db.Column(db.Text)
    photo_urls = db.Column(db.JSON)
    is_approved = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='reviews')

    def calculate_overall(self):
        ratings = [r for r in [self.food_rating, self.service_rating,
                               self.ambience_rating, self.cleanliness_rating] if r]
        self.overall_rating = sum(ratings) / len(ratings) if ratings else 0

    def to_dict(self):
        return {
            'id': self.id,
            'user': self.user.to_dict() if self.user else None,
            'food_rating': self.food_rating,
            'service_rating': self.service_rating,
            'ambience_rating': self.ambience_rating,
            'cleanliness_rating': self.cleanliness_rating,
            'overall_rating': self.overall_rating,
            'review_text': self.review_text,
            'photo_urls': self.photo_urls,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
