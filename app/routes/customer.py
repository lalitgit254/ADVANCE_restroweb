from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.menu import FoodItem, Category
from app.models.order import Order
from app.models.table import Booking
from app.models.review import Review
from app.models.loyalty import LoyaltyPoint
from app.services.order_service import OrderService
from app.services.booking_service import BookingService
from app.services.payment_service import PaymentService
from app.services.loyalty_service import LoyaltyService
from app.services.notification_service import NotificationService
from app.utils.decorators import role_required

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/dashboard')
@login_required
@role_required('customer')
def dashboard():
    recent_orders = Order.query.filter_by(customer_id=current_user.id).order_by(
        Order.created_at.desc()).limit(5).all()
    upcoming_bookings = Booking.query.filter_by(
        customer_id=current_user.id
    ).filter(Booking.status.in_(['pending', 'confirmed'])).order_by(
        Booking.booking_date).limit(3).all()
    loyalty = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
    return render_template('customer/dashboard.html',
                           recent_orders=recent_orders,
                           upcoming_bookings=upcoming_bookings,
                           loyalty=loyalty)


@customer_bp.route('/menu/<int:restaurant_id>')
@login_required
def menu(restaurant_id):
    categories = Category.query.filter_by(restaurant_id=restaurant_id, is_active=True).all()
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'name')
    filter_type = request.args.get('filter', '')

    query = FoodItem.query.filter_by(restaurant_id=restaurant_id, is_available=True)
    if search:
        query = query.filter(FoodItem.name.ilike(f'%{search}%'))
    if filter_type == 'veg':
        query = query.filter_by(is_veg=True)
    elif filter_type == 'non_veg':
        query = query.filter_by(is_veg=False)
    elif filter_type == 'special':
        query = query.filter_by(is_special=True)
    elif filter_type == 'bestseller':
        query = query.filter_by(is_bestseller=True)

    if sort == 'price_low':
        query = query.order_by(FoodItem.price)
    elif sort == 'price_high':
        query = query.order_by(FoodItem.price.desc())
    elif sort == 'rating':
        query = query.order_by(FoodItem.avg_rating.desc())
    else:
        query = query.order_by(FoodItem.name)

    foods = query.all()
    cart = OrderService.get_or_create_cart(current_user.id, restaurant_id)
    return render_template('customer/menu.html', categories=categories, foods=foods, cart=cart)


@customer_bp.route('/cart')
@login_required
def cart():
    cart = OrderService.get_or_create_cart(current_user.id)
    return render_template('customer/cart.html', cart=cart)


@customer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json() if request.is_json else request.form
    try:
        cart = OrderService.add_to_cart(
            current_user.id,
            int(data.get('food_item_id')),
            int(data.get('quantity', 1)),
            variant_id=int(data['variant_id']) if data.get('variant_id') else None,
            addons=data.get('addons'),
            special_instructions=data.get('special_instructions'),
            restaurant_id=int(data['restaurant_id']) if data.get('restaurant_id') else None,
        )
        if request.is_json:
            return jsonify({'success': True, 'cart': cart.to_dict()})
        flash('Added to cart!', 'success')
    except (ValueError, Exception) as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(str(e), 'danger')
    return redirect(request.referrer or url_for('customer.cart'))


@customer_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    from app.models.restaurant import Branch
    cart = OrderService.get_or_create_cart(current_user.id)
    if cart.items.count() == 0:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('customer.cart'))

    branches = Branch.query.filter_by(restaurant_id=cart.restaurant_id, is_active=True).all()
    loyalty = LoyaltyService.get_or_create(current_user.id)

    if request.method == 'POST':
        try:
            order = OrderService.place_order(
                current_user.id,
                order_type=request.form.get('order_type', 'dine_in'),
                branch_id=int(request.form.get('branch_id')),
                table_id=int(request.form['table_id']) if request.form.get('table_id') else None,
                delivery_address=request.form.get('delivery_address'),
                coupon_code=request.form.get('coupon_code'),
                loyalty_points=int(request.form.get('loyalty_points', 0)),
                special_instructions=request.form.get('special_instructions'),
            )
            return redirect(url_for('customer.payment', order_id=order.id))
        except ValueError as e:
            flash(str(e), 'danger')

    return render_template('customer/checkout.html', cart=cart, branches=branches, loyalty=loyalty)


@customer_bp.route('/payment/<int:order_id>', methods=['GET', 'POST'])
@login_required
def payment(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    payment = PaymentService.create_payment(order, request.form.get('method', 'upi') if request.method == 'POST' else 'upi')
    db.session.commit()

    if request.method == 'POST':
        method = request.form.get('method', 'upi')
        if method == 'cash':
            payment.status = 'completed'
            payment.payment_method = 'cash'
            order.status = 'accepted'
            db.session.commit()
            LoyaltyService.earn_points(current_user.id, order.id, order.total_amount)
            return redirect(url_for('customer.order_tracking', order_id=order.id))

        return render_template('customer/payment.html', order=order, payment=payment,
                               razorpay_key=PaymentService.get_razorpay_client() and True)

    return render_template('customer/payment.html', order=order, payment=payment)


@customer_bp.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json()
    from app.models.payment import Payment
    payment = Payment.query.filter_by(razorpay_order_id=data.get('razorpay_order_id')).first_or_404()

    if PaymentService.complete_payment(
            payment,
            data.get('razorpay_payment_id'),
            data.get('razorpay_signature')):
        LoyaltyService.earn_points(current_user.id, payment.order_id, payment.amount)
        return jsonify({'success': True, 'redirect': url_for('customer.review', order_id=payment.order_id)})
    return jsonify({'success': False}), 400


@customer_bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(
        Order.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('customer/orders.html', orders=orders)


@customer_bp.route('/orders/<int:order_id>/track')
@login_required
def order_tracking(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    return render_template('customer/order_tracking.html', order=order)


@customer_bp.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    from app.models.restaurant import Branch
    if request.method == 'POST':
        try:
            booking = BookingService.create_booking(
                current_user.id,
                int(request.form.get('branch_id')),
                datetime.strptime(request.form.get('booking_date'), '%Y-%m-%d').date(),
                datetime.strptime(request.form.get('booking_time'), '%H:%M').time(),
                int(request.form.get('guests')),
                table_id=int(request.form['table_id']) if request.form.get('table_id') else None,
                special_requests=request.form.get('special_requests'),
            )
            flash(f'Booking confirmed! Code: {booking.confirmation_code}', 'success')
            return redirect(url_for('customer.bookings'))
        except ValueError as e:
            flash(str(e), 'danger')

    user_bookings = Booking.query.filter_by(customer_id=current_user.id).order_by(
        Booking.booking_date.desc()).all()
    branches = Branch.query.filter_by(is_active=True).all()
    return render_template('customer/bookings.html', bookings=user_bookings, branches=branches)


@customer_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        BookingService.cancel_booking(booking_id, current_user.id)
        flash('Booking cancelled', 'info')
    except Exception as e:
        flash(str(e), 'danger')
    return redirect(url_for('customer.bookings'))


@customer_bp.route('/review/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review(order_id):
    order = Order.query.filter_by(id=order_id, customer_id=current_user.id).first_or_404()
    if request.method == 'POST':
        review = Review(
            user_id=current_user.id,
            order_id=order.id,
            restaurant_id=order.restaurant_id,
            food_rating=int(request.form.get('food_rating', 5)),
            service_rating=int(request.form.get('service_rating', 5)),
            ambience_rating=int(request.form.get('ambience_rating', 5)),
            cleanliness_rating=int(request.form.get('cleanliness_rating', 5)),
            review_text=request.form.get('review_text'),
        )
        review.calculate_overall()
        db.session.add(review)
        db.session.commit()
        flash('Thank you for your review!', 'success')
        return redirect(url_for('customer.dashboard'))
    return render_template('customer/review.html', order=order)


@customer_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.language = request.form.get('language', current_user.language)
        current_user.dark_mode = request.form.get('dark_mode') == 'on'
        db.session.commit()
        flash('Profile updated!', 'success')
    loyalty = LoyaltyPoint.query.filter_by(user_id=current_user.id).first()
    return render_template('customer/profile.html', loyalty=loyalty)


@customer_bp.route('/call-waiter', methods=['POST'])
@login_required
def call_waiter():
    data = request.get_json()
    NotificationService.call_waiter(
        data.get('table_id'), data.get('branch_id'), data.get('table_number')
    )
    return jsonify({'success': True})
