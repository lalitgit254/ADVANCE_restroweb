import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from flask import current_app
from app.extensions import db
from app.models.payment import Payment
from app.utils.helpers import calculate_gst


class PaymentService:
    @staticmethod
    def get_razorpay_client():
        try:
            import razorpay
            return razorpay.Client(auth=(
                current_app.config['RAZORPAY_KEY_ID'],
                current_app.config['RAZORPAY_KEY_SECRET']
            ))
        except Exception:
            return None

    @staticmethod
    def create_payment(order, method='upi'):
        gst = calculate_gst(order.subtotal)
        invoice_number = f'INV{datetime.now(timezone.utc).strftime("%Y%m%d")}{secrets.token_hex(3).upper()}'

        payment = Payment(
            order_id=order.id,
            customer_id=order.customer_id,
            amount=order.total_amount,
            payment_method=method,
            gst_amount=gst,
            invoice_number=invoice_number,
            transaction_id=secrets.token_hex(8).upper(),
        )
        db.session.add(payment)

        client = PaymentService.get_razorpay_client()
        if client and method != 'cash':
            try:
                razorpay_order = client.order.create({
                    'amount': int(float(order.total_amount) * 100),
                    'currency': 'INR',
                    'receipt': order.order_number,
                })
                payment.razorpay_order_id = razorpay_order['id']
            except Exception as e:
                current_app.logger.error('Razorpay order creation failed: %s', str(e))

        db.session.flush()
        return payment

    @staticmethod
    def verify_razorpay_signature(payment_id, order_id, signature):
        secret = current_app.config['RAZORPAY_KEY_SECRET']
        if not secret:
            return False
        body = f'{order_id}|{payment_id}'
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    @staticmethod
    def complete_payment(payment, razorpay_payment_id=None, razorpay_signature=None):
        if razorpay_payment_id and payment.razorpay_order_id:
            if not PaymentService.verify_razorpay_signature(
                    razorpay_payment_id, payment.razorpay_order_id, razorpay_signature):
                payment.status = 'failed'
                db.session.commit()
                return False

        payment.status = 'completed'
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.paid_at = datetime.now(timezone.utc)
        payment.order.status = 'completed' if payment.order.order_type != 'home_delivery' else 'out_for_delivery'
        payment.order.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return True

    @staticmethod
    def process_refund(payment, amount=None, reason=''):
        refund_amount = amount or float(payment.amount)
        client = PaymentService.get_razorpay_client()

        if client and payment.razorpay_payment_id:
            try:
                client.payment.refund(payment.razorpay_payment_id, {'amount': int(refund_amount * 100)})
            except Exception as e:
                current_app.logger.error('Refund failed: %s', str(e))
                return False

        payment.refund_amount = refund_amount
        payment.refund_reason = reason
        payment.refunded_at = datetime.now(timezone.utc)
        payment.status = 'refunded' if refund_amount >= float(payment.amount) else 'partially_refunded'
        db.session.commit()
        return True
