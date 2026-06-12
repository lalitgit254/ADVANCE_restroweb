from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.order import Order
from app.services.order_service import OrderService
from app.utils.decorators import role_required

chef_bp = Blueprint('chef', __name__)


@chef_bp.route('/dashboard')
@login_required
@role_required('chef', 'admin', 'manager')
def dashboard():
    orders = Order.query.filter(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status.in_(['accepted', 'preparing', 'ready'])
    ).order_by(Order.priority.desc(), Order.created_at).all()
    return render_template('chef/dashboard.html', orders=orders)


@chef_bp.route('/kds')
@login_required
@role_required('chef', 'admin', 'manager')
def kds():
    orders = Order.query.filter(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status.in_(['accepted', 'preparing'])
    ).order_by(Order.priority.desc(), Order.created_at).all()
    return render_template('chef/kds.html', orders=orders)


@chef_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('chef', 'admin', 'manager')
def update_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    OrderService.update_status(order, new_status)
    if not order.assigned_chef_id:
        order.assigned_chef_id = current_user.id
    flash(f'Order marked as {new_status}', 'success')
    return redirect(request.referrer or url_for('chef.dashboard'))
