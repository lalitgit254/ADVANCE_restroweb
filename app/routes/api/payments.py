from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.routes.api import api_bp
from app.models.order import Order
from app.models.payment import Payment
from app.services.payment_service import PaymentService


@api_bp.route('/payments/create', methods=['POST'])
@jwt_required()
def api_create_payment():
    """Create a payment for an order
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    order = Order.query.filter_by(id=data['order_id'], customer_id=user_id).first_or_404()
    payment = PaymentService.create_payment(order, data.get('method', 'upi'))
    db.session.commit()
    return jsonify({
        'payment': payment.to_dict(),
        'razorpay_key': current_app.config.get('RAZORPAY_KEY_ID'),
        'razorpay_order_id': payment.razorpay_order_id,
    })


@api_bp.route('/payments/verify', methods=['POST'])
@jwt_required()
def api_verify_payment():
    """Verify Razorpay payment
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    """
    data = request.get_json()
    payment = Payment.query.filter_by(razorpay_order_id=data.get('razorpay_order_id')).first_or_404()
    success = PaymentService.complete_payment(
        payment, data.get('razorpay_payment_id'), data.get('razorpay_signature'))
    if success:
        from app.services.loyalty_service import LoyaltyService
        LoyaltyService.earn_points(payment.customer_id, payment.order_id, payment.amount)
        return jsonify({'success': True, 'payment': payment.to_dict()})
    return jsonify({'success': False}), 400
