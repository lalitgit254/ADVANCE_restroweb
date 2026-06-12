from flask import Blueprint, render_template, request
from app.models.restaurant import Restaurant
from app.models.menu import FoodItem, Category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    restaurants = Restaurant.query.filter_by(is_active=True).limit(6).all()
    return render_template('main/index.html', restaurants=restaurants)


@main_bp.route('/restaurant/<slug>')
def restaurant_profile(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, is_active=True).first_or_404()
    categories = Category.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    specials = FoodItem.query.filter_by(
        restaurant_id=restaurant.id, is_special=True, is_available=True
    ).limit(6).all()
    bestsellers = FoodItem.query.filter_by(
        restaurant_id=restaurant.id, is_bestseller=True, is_available=True
    ).limit(6).all()
    return render_template('main/restaurant.html',
                           restaurant=restaurant, categories=categories,
                           specials=specials, bestsellers=bestsellers)


@main_bp.route('/menu/qr/<qr_code>')
def qr_menu(qr_code):
    from app.models.table import Table
    table = Table.query.filter_by(qr_code=qr_code, is_active=True).first_or_404()
    restaurant = table.branch.restaurant
    categories = Category.query.filter_by(restaurant_id=restaurant.id, is_active=True).all()
    return render_template('customer/qr_menu.html',
                           table=table, restaurant=restaurant, categories=categories)


@main_bp.route('/faq')
def faq():
    from app.models.support import FAQ
    faqs = FAQ.query.filter_by(is_active=True).order_by(FAQ.sort_order).all()
    return render_template('main/faq.html', faqs=faqs)


@main_bp.route('/set-language/<lang>')
def set_language(lang):
    from flask import session, redirect, request
    if lang in ('en', 'hi'):
        session['language'] = lang
    return redirect(request.referrer or '/')
