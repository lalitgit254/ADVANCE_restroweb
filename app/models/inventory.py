from datetime import datetime, timezone
from app.extensions import db


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='suppliers')
    inventory_items = db.relationship('Inventory', backref='supplier', lazy='dynamic')
    purchases = db.relationship('Purchase', backref='supplier', lazy='dynamic')


class Inventory(db.Model):
    __tablename__ = 'inventory'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    current_stock = db.Column(db.Numeric(10, 2), default=0)
    min_stock_level = db.Column(db.Numeric(10, 2), default=0)
    max_stock_level = db.Column(db.Numeric(10, 2))
    cost_per_unit = db.Column(db.Numeric(10, 2))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    expiry_date = db.Column(db.Date)
    last_restocked = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='inventory_items')
    branch = db.relationship('Branch', backref='inventory_items')

    @property
    def is_low_stock(self):
        return float(self.current_stock) <= float(self.min_stock_level)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit,
            'current_stock': float(self.current_stock),
            'min_stock_level': float(self.min_stock_level),
            'is_low_stock': self.is_low_stock,
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
        }


class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    invoice_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='purchases')
    inventory_item = db.relationship('Inventory', backref='purchases')
