from datetime import datetime, timezone
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    food_items = db.relationship('FoodItem', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }


class FoodItem(db.Model):
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500))
    is_veg = db.Column(db.Boolean, default=True)
    preparation_time = db.Column(db.Integer, default=15)
    is_available = db.Column(db.Boolean, default=True)
    is_special = db.Column(db.Boolean, default=False)
    is_bestseller = db.Column(db.Boolean, default=False)
    discount_percent = db.Column(db.Numeric(5, 2), default=0)
    avg_rating = db.Column(db.Float, default=0)
    total_orders = db.Column(db.Integer, default=0)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    images = db.relationship('FoodImage', backref='food_item', lazy='dynamic', cascade='all, delete-orphan')
    variants = db.relationship('FoodVariant', backref='food_item', lazy='dynamic', cascade='all, delete-orphan')
    addons = db.relationship('FoodAddon', backref='food_item', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='food_item', lazy='dynamic')

    @property
    def discounted_price(self):
        if self.discount_percent:
            return float(self.price) * (1 - float(self.discount_percent) / 100)
        return float(self.price)

    def to_dict(self, detailed=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'discounted_price': self.discounted_price,
            'image_url': self.image_url,
            'is_veg': self.is_veg,
            'preparation_time': self.preparation_time,
            'is_available': self.is_available,
            'is_special': self.is_special,
            'is_bestseller': self.is_bestseller,
            'discount_percent': float(self.discount_percent) if self.discount_percent else 0,
            'avg_rating': self.avg_rating,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
        }
        if detailed:
            data['images'] = [img.to_dict() for img in self.images]
            data['variants'] = [v.to_dict() for v in self.variants]
            data['addons'] = [a.to_dict() for a in self.addons]
        return data


class FoodImage(db.Model):
    __tablename__ = 'food_images'

    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {'id': self.id, 'image_url': self.image_url, 'is_primary': self.is_primary}


class FoodVariant(db.Model):
    __tablename__ = 'food_variants'

    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    price_adjustment = db.Column(db.Numeric(10, 2), default=0)
    is_default = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price_adjustment': float(self.price_adjustment),
            'is_default': self.is_default,
            'is_available': self.is_available,
        }


class FoodAddon(db.Model):
    __tablename__ = 'food_addons'

    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    is_available = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'price': float(self.price), 'is_available': self.is_available}
