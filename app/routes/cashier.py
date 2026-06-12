from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.order import Order
from app.models.payment import Payment
from app.services.payment_service import PaymentService
from app.utils.decorators import role_required
from app.utils.pdf_generator import generate_invoice_pdf

cashier_bp = Blueprint('cashier', __name__)


@cashier_bp.route('/dashboard')
@login_required
@role_required('cashier', 'admin', 'manager')
def dashboard():
    today = datetime.now(timezone.utc).date()
    pending_payments = Payment.query.join(Order).filter(
        Order.restaurant_id == current_user.restaurant_id,
        Payment.status == 'pending'
    ).all()
    daily_total = db.session.query(func.sum(Payment.amount)).join(Order).filter(
        Order.restaurant_id == current_user.restaurant_id,
        Payment.status == 'completed',
        func.date(Payment.paid_at) == today
    ).scalar() or 0
    return render_template('cashier/dashboard.html',
                           pending_payments=pending_payments, daily_total=daily_total)


@cashier_bp.route('/bill/<int:order_id>')
@login_required
@role_required('cashier', 'admin', 'manager')
def generate_bill(order_id):
    order = Order.query.get_or_404(order_id)
    payment = Payment.query.filter_by(order_id=order.id).first()
    if not payment:
        payment = PaymentService.create_payment(order, 'cash')
        db.session.commit()
    restaurant = order.restaurant
    pdf = generate_invoice_pdf(order, payment, restaurant)
    return send_file(pdf, mimetype='application/pdf',
                     as_attachment=True, download_name=f'bill_{order.order_number}.pdf')


@cashier_bp.route('/refund/<int:payment_id>', methods=['POST'])
@login_required
@role_required('cashier', 'admin', 'manager')
def refund(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    reason = request.form.get('reason', '')
    if PaymentService.process_refund(payment, reason=reason):
        flash('Refund processed', 'success')
    else:
        flash('Refund failed', 'danger')
    return redirect(url_for('cashier.dashboard'))
