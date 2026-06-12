from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.order import Order
from app.models.table import Table
from app.services.order_service import OrderService
from app.utils.decorators import role_required

waiter_bp = Blueprint('waiter', __name__)


@waiter_bp.route('/dashboard')
@login_required
@role_required('waiter', 'admin', 'manager')
def dashboard():
    ready_orders = Order.query.filter(
        Order.restaurant_id == current_user.restaurant_id,
        Order.status == 'ready',
        Order.order_type == 'dine_in'
    ).all()
    assigned = Order.query.filter_by(
        assigned_waiter_id=current_user.id,
        status='served'
    ).all()
    tables = Table.query.join(Table.branch).filter(
        Table.branch.has(restaurant_id=current_user.restaurant_id)
    ).all() if current_user.restaurant_id else []
    return render_template('waiter/dashboard.html',
                           ready_orders=ready_orders, assigned=assigned, tables=tables)


@waiter_bp.route('/orders/<int:order_id>/serve', methods=['POST'])
@login_required
@role_required('waiter', 'admin', 'manager')
def serve_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.assigned_waiter_id = current_user.id
    OrderService.update_status(order, 'served')
    flash('Order served!', 'success')
    return redirect(url_for('waiter.dashboard'))
