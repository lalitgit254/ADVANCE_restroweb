from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.order import Order
from app.models.table import Table, Booking
from app.models.menu import Category, FoodItem, FoodVariant, FoodAddon
from app.models.user import User
from app.models.staff import Staff
from app.models.inventory import Inventory, Supplier
from app.models.payment import Payment
from app.models.review import Review
from app.services.order_service import OrderService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.cloudinary_service import CloudinaryService
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    restaurant_id = current_user.restaurant_id
    today = datetime.now(timezone.utc).date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    base = Order.query.filter_by(restaurant_id=restaurant_id) if restaurant_id else Order.query

    total_revenue = db.session.query(func.sum(Order.total_amount)).filter(
        Order.restaurant_id == restaurant_id, Order.status == 'completed'
    ).scalar() or 0

    daily_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.restaurant_id == restaurant_id,
        func.date(Order.created_at) == today
    ).scalar() or 0

    weekly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.restaurant_id == restaurant_id,
        func.date(Order.created_at) >= week_ago
    ).scalar() or 0

    monthly_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.restaurant_id == restaurant_id,
        func.date(Order.created_at) >= month_ago
    ).scalar() or 0

    active_orders = Order.query.filter(
        Order.restaurant_id == restaurant_id,
        Order.status.in_(['pending', 'accepted', 'preparing', 'ready'])
    ).count()

    active_bookings = Booking.query.filter(
        Booking.status.in_(['pending', 'confirmed']),
        func.date(Booking.booking_date) >= today
    ).count()

    low_stock = Inventory.query.filter(
        Inventory.restaurant_id == restaurant_id,
        Inventory.current_stock <= Inventory.min_stock_level
    ).count() if restaurant_id else 0

    total_customers = User.query.filter_by(role='customer').count()

    return render_template('admin/dashboard.html',
                           total_revenue=total_revenue, daily_sales=daily_sales,
                           weekly_sales=weekly_sales, monthly_sales=monthly_sales,
                           active_orders=active_orders, active_bookings=active_bookings,
                           low_stock=low_stock, total_customers=total_customers)


@admin_bp.route('/foods')
@login_required
@admin_required
def foods():
    items = FoodItem.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    categories = Category.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    return render_template('admin/foods.html', items=items, categories=categories)


@admin_bp.route('/foods/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_food():
    categories = Category.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    if request.method == 'POST':
        food = FoodItem(
            restaurant_id=current_user.restaurant_id,
            category_id=int(request.form.get('category_id')),
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            is_veg=request.form.get('is_veg') == 'on',
            preparation_time=int(request.form.get('preparation_time', 15)),
            is_special=request.form.get('is_special') == 'on',
            is_bestseller=request.form.get('is_bestseller') == 'on',
            discount_percent=float(request.form.get('discount_percent', 0)),
        )
        if 'image' in request.files and request.files['image'].filename:
            food.image_url = CloudinaryService.upload_image(request.files['image'], 'foods')
        db.session.add(food)
        db.session.commit()
        flash('Food item added!', 'success')
        return redirect(url_for('admin.foods'))
    return render_template('admin/food_form.html', categories=categories, food=None)


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status = request.args.get('status', '')
    query = Order.query.filter_by(restaurant_id=current_user.restaurant_id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/orders.html', orders=orders, status=status)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order = Order.query.filter_by(id=order_id, restaurant_id=current_user.restaurant_id).first_or_404()
    new_status = request.form.get('status')
    chef_id = request.form.get('chef_id')
    waiter_id = request.form.get('waiter_id')

    if chef_id:
        order.assigned_chef_id = int(chef_id)
    if waiter_id:
        order.assigned_waiter_id = int(waiter_id)

    OrderService.update_status(order, new_status)
    flash(f'Order status updated to {new_status}', 'success')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    bookings = Booking.query.order_by(Booking.booking_date.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/bookings.html', bookings=bookings)


@admin_bp.route('/bookings/<int:booking_id>/action', methods=['POST'])
@login_required
@admin_required
def booking_action(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    action = request.form.get('action')
    if action == 'approve':
        booking.status = 'confirmed'
    elif action == 'reject':
        booking.status = 'cancelled'
        if booking.table_id:
            table = Table.query.get(booking.table_id)
            if table:
                table.status = 'available'
    db.session.commit()
    flash(f'Booking {action}d', 'success')
    return redirect(url_for('admin.bookings'))


@admin_bp.route('/tables')
@login_required
@admin_required
def tables():
    from app.models.restaurant import Branch
    branch_id = request.args.get('branch_id', type=int)
    query = Table.query
    if branch_id:
        query = query.filter_by(branch_id=branch_id)
    tables = query.all()
    branches = Branch.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    return render_template('admin/tables.html', tables=tables, branches=branches)


@admin_bp.route('/tables/add', methods=['POST'])
@login_required
@admin_required
def add_table():
    table = Table(
        branch_id=int(request.form.get('branch_id')),
        table_number=request.form.get('table_number'),
        capacity=int(request.form.get('capacity')),
        table_type=request.form.get('table_type'),
        location=request.form.get('location'),
    )
    table.generate_qr_code()
    db.session.add(table)
    db.session.commit()
    flash('Table added!', 'success')
    return redirect(url_for('admin.tables'))


@admin_bp.route('/staff')
@login_required
@admin_required
def staff():
    staff_list = Staff.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    return render_template('admin/staff.html', staff_list=staff_list)


@admin_bp.route('/inventory')
@login_required
@admin_required
def inventory():
    items = Inventory.query.filter_by(restaurant_id=current_user.restaurant_id).all()
    return render_template('admin/inventory.html', items=items)


@admin_bp.route('/payments')
@login_required
@admin_required
def payments():
    payments = Payment.query.join(Order).filter(
        Order.restaurant_id == current_user.restaurant_id
    ).order_by(Payment.created_at.desc()).paginate(
        page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('admin/payments.html', payments=payments)


@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    reviews = Review.query.filter_by(restaurant_id=current_user.restaurant_id).order_by(
        Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)


@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    return render_template('admin/analytics.html')
