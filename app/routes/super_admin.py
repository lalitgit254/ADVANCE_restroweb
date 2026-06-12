from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func
from app.extensions import db
from app.models.restaurant import Restaurant, Branch, SubscriptionPlan
from app.models.user import User
from app.models.order import Order
from app.models.payment import Payment
from app.utils.decorators import role_required

super_admin_bp = Blueprint('super_admin', __name__)


@super_admin_bp.route('/dashboard')
@login_required
@role_required('super_admin')
def dashboard():
    total_restaurants = Restaurant.query.count()
    total_users = User.query.count()
    total_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'completed').scalar() or 0
    active_orders = Order.query.filter(
        Order.status.in_(['pending', 'accepted', 'preparing', 'ready'])).count()
    restaurants = Restaurant.query.order_by(Restaurant.created_at.desc()).limit(10).all()
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('super_admin/dashboard.html',
                           total_restaurants=total_restaurants,
                           total_users=total_users,
                           total_revenue=total_revenue,
                           active_orders=active_orders,
                           restaurants=restaurants,
                           plans=plans)


@super_admin_bp.route('/restaurants')
@login_required
@role_required('super_admin')
def restaurants():
    restaurants = Restaurant.query.order_by(Restaurant.name).all()
    return render_template('super_admin/restaurants.html', restaurants=restaurants)


@super_admin_bp.route('/restaurants/add', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def add_restaurant():
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        import re
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        restaurant = Restaurant(
            name=name,
            slug=slug,
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            subscription_plan_id=int(request.form['plan_id']) if request.form.get('plan_id') else None,
        )
        db.session.add(restaurant)
        db.session.flush()

        branch = Branch(
            restaurant_id=restaurant.id,
            name=f'{name} - Main Branch',
            address=restaurant.address,
            phone=restaurant.phone,
        )
        db.session.add(branch)
        db.session.commit()
        flash('Restaurant created!', 'success')
        return redirect(url_for('super_admin.restaurants'))
    return render_template('super_admin/restaurant_form.html', plans=plans)


@super_admin_bp.route('/admins/create', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def create_admin():
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        from app.services.auth_service import AuthService
        user = AuthService.register(
            request.form.get('email'),
            request.form.get('password'),
            request.form.get('first_name'),
            request.form.get('last_name'),
        )
        user.role = request.form.get('role', 'admin')
        user.restaurant_id = int(request.form.get('restaurant_id'))
        user.is_verified = True
        user.email_verified = True
        db.session.commit()
        flash('Admin account created!', 'success')
        return redirect(url_for('super_admin.dashboard'))
    return render_template('super_admin/create_admin.html', restaurants=restaurants)
