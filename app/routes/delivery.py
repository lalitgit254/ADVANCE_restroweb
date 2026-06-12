from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.order import DeliveryOrder
from app.services.order_service import OrderService
from app.services.notification_service import NotificationService
from app.utils.decorators import role_required

delivery_bp = Blueprint('delivery', __name__)


@delivery_bp.route('/dashboard')
@login_required
@role_required('delivery_boy', 'admin', 'manager')
def dashboard():
    active = DeliveryOrder.query.filter_by(
        delivery_boy_id=current_user.id
    ).filter(DeliveryOrder.status.in_(['pending', 'picked_up', 'in_transit'])).all()

    available = DeliveryOrder.query.filter_by(
        delivery_boy_id=None, status='pending'
    ).all()
    return render_template('delivery/dashboard.html', active=active, available=available)


@delivery_bp.route('/accept/<int:delivery_id>', methods=['POST'])
@login_required
@role_required('delivery_boy')
def accept_delivery(delivery_id):
    delivery = DeliveryOrder.query.get_or_404(delivery_id)
    delivery.delivery_boy_id = current_user.id
    delivery.status = 'picked_up'
    delivery.picked_up_at = datetime.now(timezone.utc)
    delivery.order.status = 'out_for_delivery'
    db.session.commit()
    NotificationService.notify_order_update(delivery.order)
    flash('Delivery accepted!', 'success')
    return redirect(url_for('delivery.dashboard'))


@delivery_bp.route('/complete/<int:delivery_id>', methods=['POST'])
@login_required
@role_required('delivery_boy')
def complete_delivery(delivery_id):
    delivery = DeliveryOrder.query.get_or_404(delivery_id)
    delivery.status = 'delivered'
    delivery.delivered_at = datetime.now(timezone.utc)
    OrderService.update_status(delivery.order, 'delivered')
    flash('Delivery completed!', 'success')
    return redirect(url_for('delivery.dashboard'))
