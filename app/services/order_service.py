from datetime import datetime, timezone
from decimal import Decimal
from app.extensions import db
from app.models.order import Cart, CartItem, Order, OrderItem, DeliveryOrder
from app.models.menu import FoodItem
from app.models.payment import Coupon
from app.services.notification_service import NotificationService
from app.services.loyalty_service import LoyaltyService
from app.utils.helpers import calculate_gst


class OrderService:
    @staticmethod
    def get_or_create_cart(user_id, restaurant_id=None):
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id, restaurant_id=restaurant_id)
            db.session.add(cart)
            db.session.flush()
        return cart

    @staticmethod
    def add_to_cart(user_id, food_item_id, quantity=1, variant_id=None,
                    addons=None, special_instructions=None, restaurant_id=None):
        cart = OrderService.get_or_create_cart(user_id, restaurant_id)
        food_item = FoodItem.query.get_or_404(food_item_id)

        if not food_item.is_available:
            raise ValueError('Food item is not available')

        existing = CartItem.query.filter_by(
            cart_id=cart.id, food_item_id=food_item_id, variant_id=variant_id
        ).first()

        if existing:
            existing.quantity += quantity
            if special_instructions:
                existing.special_instructions = special_instructions
            if addons:
                existing.addons = addons
        else:
            item = CartItem(
                cart_id=cart.id,
                food_item_id=food_item_id,
                variant_id=variant_id,
                quantity=quantity,
                special_instructions=special_instructions,
                addons=addons,
            )
            db.session.add(item)

        cart.restaurant_id = restaurant_id or food_item.restaurant_id
        db.session.commit()
        return cart

    @staticmethod
    def place_order(user_id, order_type, branch_id, table_id=None,
                    delivery_address=None, coupon_code=None, loyalty_points=0,
                    special_instructions=None):
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart or cart.items.count() == 0:
            raise ValueError('Cart is empty')

        subtotal = Decimal(str(cart.total))
        discount = Decimal('0')
        tax = Decimal(str(calculate_gst(subtotal)))
        delivery_charge = Decimal('50') if order_type == 'home_delivery' else Decimal('0')

        if coupon_code:
            coupon = Coupon.query.filter_by(code=coupon_code, is_active=True).first()
            if coupon and coupon.is_valid(subtotal):
                discount = Decimal(str(coupon.calculate_discount(subtotal)))
                coupon.used_count += 1

        if loyalty_points > 0:
            if LoyaltyService.redeem_points(user_id, loyalty_points):
                discount += Decimal(str(loyalty_points))

        total = subtotal + tax + delivery_charge - discount

        order = Order(
            customer_id=user_id,
            restaurant_id=cart.restaurant_id,
            branch_id=branch_id,
            table_id=table_id,
            order_type=order_type,
            subtotal=subtotal,
            tax_amount=tax,
            discount_amount=discount,
            delivery_charge=delivery_charge,
            total_amount=total,
            special_instructions=special_instructions,
            delivery_address=delivery_address,
            coupon_code=coupon_code,
            loyalty_points_used=loyalty_points,
        )
        order.generate_order_number()
        db.session.add(order)
        db.session.flush()

        for cart_item in cart.items:
            order_item = OrderItem(
                order_id=order.id,
                food_item_id=cart_item.food_item_id,
                variant_id=cart_item.variant_id,
                food_name=cart_item.food_item.name,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                total_price=cart_item.subtotal,
                special_instructions=cart_item.special_instructions,
                addons=cart_item.addons,
            )
            db.session.add(order_item)
            cart_item.food_item.total_orders += cart_item.quantity

        if order_type == 'home_delivery' and delivery_address:
            delivery = DeliveryOrder(
                order_id=order.id,
                delivery_address=delivery_address,
            )
            db.session.add(delivery)

        CartItem.query.filter_by(cart_id=cart.id).delete()
        db.session.commit()

        NotificationService.notify_order_update(order)
        socketio_emit_new_order(order)
        return order

    @staticmethod
    def update_status(order, new_status, user_id=None):
        order.status = new_status
        now = datetime.now(timezone.utc)

        status_timestamps = {
            'accepted': 'accepted_at',
            'preparing': 'preparing_at',
            'ready': 'ready_at',
            'served': 'served_at',
            'completed': 'completed_at',
            'cancelled': 'cancelled_at',
        }
        if new_status in status_timestamps:
            setattr(order, status_timestamps[new_status], now)

        db.session.commit()
        NotificationService.notify_order_update(order)

        if new_status == 'ready':
            NotificationService.notify_staff(
                f'branch_{order.branch_id}_kitchen', 'order_ready', order.to_dict()
            )
        return order


def socketio_emit_new_order(order):
    from app.extensions import socketio
    socketio.emit('new_order', order.to_dict(detailed=True),
                  room=f'restaurant_{order.restaurant_id}')
    socketio.emit('new_order', order.to_dict(detailed=True),
                  room=f'branch_{order.branch_id}_kitchen')
