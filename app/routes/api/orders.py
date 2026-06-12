from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes.api import api_bp
from app.models.order import Order, Cart
from app.services.order_service import OrderService


@api_bp.route('/cart', methods=['GET'])
@jwt_required()
def api_get_cart():
    """Get current user's cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    cart = OrderService.get_or_create_cart(user_id)
    return jsonify(cart.to_dict())


@api_bp.route('/cart/add', methods=['POST'])
@jwt_required()
def api_add_to_cart():
    """Add item to cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        cart = OrderService.add_to_cart(
            user_id, data['food_item_id'], data.get('quantity', 1),
            variant_id=data.get('variant_id'),
            addons=data.get('addons'),
            special_instructions=data.get('special_instructions'),
            restaurant_id=data.get('restaurant_id'),
        )
        return jsonify(cart.to_dict())
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
@jwt_required()
def api_remove_from_cart(item_id):
    """Remove item from cart
    ---
    tags:
      - Cart
    security:
      - Bearer: []
    """
    from app.models.order import CartItem
    user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=user_id).first()
    if cart:
        item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
        if item:
            from app.extensions import db
            db.session.delete(item)
            db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/orders', methods=['POST'])
@jwt_required()
def api_place_order():
    """Place an order
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        order = OrderService.place_order(
            user_id,
            order_type=data.get('order_type', 'dine_in'),
            branch_id=data['branch_id'],
            table_id=data.get('table_id'),
            delivery_address=data.get('delivery_address'),
            coupon_code=data.get('coupon_code'),
            loyalty_points=data.get('loyalty_points', 0),
            special_instructions=data.get('special_instructions'),
        )
        return jsonify(order.to_dict(detailed=True)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/orders', methods=['GET'])
@jwt_required()
def api_list_orders():
    """List user's orders
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(customer_id=user_id).order_by(
        Order.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return jsonify({
        'orders': [o.to_dict() for o in orders.items],
        'total': orders.total,
        'pages': orders.pages,
        'current_page': page,
    })


@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def api_order_detail(order_id):
    """Get order details
    ---
    tags:
      - Orders
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    order = Order.query.filter_by(id=order_id, customer_id=user_id).first_or_404()
    return jsonify(order.to_dict(detailed=True))
