from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes.api import api_bp
from app.models.menu import Category, FoodItem
from app.models.restaurant import Restaurant


@api_bp.route('/restaurants', methods=['GET'])
def api_restaurants():
    """List all active restaurants
    ---
    tags:
      - Restaurants
    """
    restaurants = Restaurant.query.filter_by(is_active=True).all()
    return jsonify([r.to_dict() for r in restaurants])


@api_bp.route('/restaurants/<int:restaurant_id>/menu', methods=['GET'])
def api_menu(restaurant_id):
    """Get restaurant menu with filters
    ---
    tags:
      - Menu
    parameters:
      - name: search
        in: query
        type: string
      - name: category_id
        in: query
        type: integer
      - name: filter
        in: query
        type: string
        enum: [veg, non_veg, special, bestseller]
    """
    query = FoodItem.query.filter_by(restaurant_id=restaurant_id, is_available=True)
    search = request.args.get('search')
    category_id = request.args.get('category_id', type=int)
    filter_type = request.args.get('filter')

    if search:
        query = query.filter(FoodItem.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if filter_type == 'veg':
        query = query.filter_by(is_veg=True)
    elif filter_type == 'non_veg':
        query = query.filter_by(is_veg=False)
    elif filter_type == 'special':
        query = query.filter_by(is_special=True)
    elif filter_type == 'bestseller':
        query = query.filter_by(is_bestseller=True)

    foods = query.all()
    categories = Category.query.filter_by(restaurant_id=restaurant_id, is_active=True).all()
    return jsonify({
        'categories': [c.to_dict() for c in categories],
        'items': [f.to_dict(detailed=True) for f in foods],
    })


@api_bp.route('/menu/<int:food_id>', methods=['GET'])
def api_food_detail(food_id):
    """Get food item details
    ---
    tags:
      - Menu
    """
    food = FoodItem.query.get_or_404(food_id)
    return jsonify(food.to_dict(detailed=True))
