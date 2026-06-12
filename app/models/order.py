from datetime import datetime, timezone
from app.extensions import db
import secrets


class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'))
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')
    table = db.relationship('Table', backref='carts')

    @property
    def total(self):
        return sum(item.subtotal for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'items': [item.to_dict() for item in self.items],
            'total': self.total,
            'item_count': self.items.count(),
        }


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('food_variants.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    special_instructions = db.Column(db.Text)
    addons = db.Column(db.JSON)

    food_item = db.relationship('FoodItem')
    variant = db.relationship('FoodVariant')

    @property
    def unit_price(self):
        base = self.food_item.discounted_price if self.food_item else 0
        if self.variant:
            base += float(self.variant.price_adjustment)
        if self.addons:
            for addon in self.addons:
                base += addon.get('price', 0)
        return base

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def to_dict(self):
        return {
            'id': self.id,
            'food_item': self.food_item.to_dict() if self.food_item else None,
            'variant': self.variant.to_dict() if self.variant else None,
            'quantity': self.quantity,
            'special_instructions': self.special_instructions,
            'addons': self.addons,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
        }


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    order_type = db.Column(db.String(20), nullable=False, default='dine_in')
    status = db.Column(db.String(20), default='pending', index=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    delivery_charge = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    special_instructions = db.Column(db.Text)
    delivery_address = db.Column(db.Text)
    assigned_chef_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    priority = db.Column(db.Boolean, default=False)
    coupon_code = db.Column(db.String(50))
    loyalty_points_used = db.Column(db.Integer, default=0)
    loyalty_points_earned = db.Column(db.Integer, default=0)
    estimated_time = db.Column(db.Integer)
    accepted_at = db.Column(db.DateTime)
    preparing_at = db.Column(db.DateTime)
    ready_at = db.Column(db.DateTime)
    served_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    cancel_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    restaurant = db.relationship('Restaurant', backref='orders')
    table = db.relationship('Table', backref='orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False)
    delivery = db.relationship('DeliveryOrder', backref='order', uselist=False)
    review = db.relationship('Review', backref='order', uselist=False)
    chef = db.relationship('User', foreign_keys=[assigned_chef_id])
    waiter = db.relationship('User', foreign_keys=[assigned_waiter_id])

    STATUSES = ['pending', 'accepted', 'preparing', 'ready', 'served',
                'out_for_delivery', 'delivered', 'completed', 'cancelled']
    ORDER_TYPES = ['dine_in', 'takeaway', 'home_delivery']

    def generate_order_number(self):
        self.order_number = f'ORD{datetime.now(timezone.utc).strftime("%Y%m%d")}{secrets.token_hex(3).upper()}'

    def to_dict(self, detailed=False):
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'order_type': self.order_type,
            'status': self.status,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'delivery_charge': float(self.delivery_charge),
            'total_amount': float(self.total_amount),
            'priority': self.priority,
            'estimated_time': self.estimated_time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if detailed:
            data['items'] = [item.to_dict() for item in self.items]
            data['customer'] = self.customer.to_dict() if self.customer else None
            data['table'] = self.table.to_dict() if self.table else None
            data['payment'] = self.payment.to_dict() if self.payment else None
        return data


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('food_variants.id'), nullable=True)
    food_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    special_instructions = db.Column(db.Text)
    addons = db.Column(db.JSON)

    food_item = db.relationship('FoodItem')
    variant = db.relationship('FoodVariant')

    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'special_instructions': self.special_instructions,
            'addons': self.addons,
        }


class DeliveryOrder(db.Model):
    __tablename__ = 'delivery_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    delivery_boy_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    pickup_address = db.Column(db.Text)
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_latitude = db.Column(db.Float)
    delivery_longitude = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')
    picked_up_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    estimated_delivery = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    delivery_boy = db.relationship('User', backref='deliveries')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'delivery_boy_id': self.delivery_boy_id,
            'delivery_address': self.delivery_address,
            'status': self.status,
            'picked_up_at': self.picked_up_at.isoformat() if self.picked_up_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
        }
