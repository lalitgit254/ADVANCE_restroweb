"""Seed database with sample data for development."""
import os
from app import create_app
from app.extensions import db
from app.models import *

app = create_app('development')

SAMPLE_FOODS = [
    ('Paneer Tikka', 'Grilled cottage cheese with spices', 280, True, 'starters'),
    ('Chicken Wings', 'Crispy fried chicken wings', 320, False, 'starters'),
    ('Butter Chicken', 'Creamy tomato curry with tender chicken', 380, False, 'main_course'),
    ('Dal Makhani', 'Slow-cooked black lentils', 260, True, 'main_course'),
    ('Margherita Pizza', 'Classic tomato and mozzarella', 350, True, 'fast_food'),
    ('Veg Burger', 'Patty with fresh vegetables', 180, True, 'fast_food'),
    ('Mango Lassi', 'Refreshing yogurt drink', 120, True, 'beverages'),
    ('Cold Coffee', 'Iced blended coffee', 150, True, 'beverages'),
    ('Gulab Jamun', 'Sweet milk dumplings', 100, True, 'desserts'),
    ('Chocolate Brownie', 'Warm brownie with ice cream', 180, True, 'desserts'),
]

CATEGORY_MAP = {
    'starters': 'Starters',
    'main_course': 'Main Course',
    'fast_food': 'Fast Food',
    'beverages': 'Beverages',
    'desserts': 'Desserts',
}


def seed():
    with app.app_context():
        db.create_all()

        if User.query.filter_by(email='admin@restaurantpro.com').first():
            print('Database already seeded.')
            return

        plan = SubscriptionPlan(
            name='Professional',
            description='Full-featured plan for restaurants',
            price_monthly=2999,
            price_yearly=29990,
            max_branches=5,
            max_staff=50,
            features={'analytics': True, 'inventory': True, 'loyalty': True},
        )
        db.session.add(plan)
        db.session.flush()

        restaurant = Restaurant(
            name='Spice Garden',
            slug='spice-garden',
            email='info@spicegarden.com',
            phone='+91 9876543210',
            address='123 Food Street, Connaught Place',
            city='New Delhi',
            state='Delhi',
            pincode='110001',
            latitude=28.6315,
            longitude=77.2167,
            opening_hours={
                'monday': '11:00-23:00', 'tuesday': '11:00-23:00',
                'wednesday': '11:00-23:00', 'thursday': '11:00-23:00',
                'friday': '11:00-00:00', 'saturday': '11:00-00:00',
                'sunday': '11:00-23:00',
            },
            social_links={'facebook': '#', 'instagram': '#'},
            gst_number='07AABCU9603R1ZM',
            subscription_plan_id=plan.id,
        )
        db.session.add(restaurant)
        db.session.flush()

        branch = Branch(
            restaurant_id=restaurant.id,
            name='Spice Garden - CP',
            address=restaurant.address,
            phone=restaurant.phone,
            latitude=restaurant.latitude,
            longitude=restaurant.longitude,
        )
        db.session.add(branch)
        db.session.flush()

        super_admin = User(
            email='superadmin@restaurantpro.com',
            first_name='Super', last_name='Admin',
            role='super_admin', is_verified=True, email_verified=True,
            referral_code='SUPER001',
        )
        super_admin.set_password('Admin@123')
        db.session.add(super_admin)

        admin = User(
            email='admin@restaurantpro.com',
            first_name='Restaurant', last_name='Admin',
            role='admin', restaurant_id=restaurant.id, branch_id=branch.id,
            is_verified=True, email_verified=True, referral_code='ADMIN001',
        )
        admin.set_password('Admin@123')
        db.session.add(admin)

        for role, fname in [('chef', 'Chef'), ('waiter', 'Waiter'),
                            ('cashier', 'Cashier'), ('delivery_boy', 'Delivery')]:
            user = User(
                email=f'{role}@restaurantpro.com',
                first_name=fname, last_name='User',
                role=role, restaurant_id=restaurant.id, branch_id=branch.id,
                is_verified=True, email_verified=True,
                referral_code=role.upper()[:8],
            )
            user.set_password('Staff@123')
            db.session.add(user)
            db.session.flush()
            staff = Staff(
                user_id=user.id, restaurant_id=restaurant.id,
                branch_id=branch.id, employee_id=f'EMP{user.id:04d}',
                designation=role.replace('_', ' ').title(),
            )
            db.session.add(staff)

        customer = User(
            email='customer@restaurantpro.com',
            first_name='John', last_name='Doe',
            role='customer', is_verified=True, email_verified=True,
            referral_code='CUST001',
        )
        customer.set_password('Customer@123')
        db.session.add(customer)
        db.session.flush()

        LoyaltyPoint(user_id=customer.id, restaurant_id=restaurant.id, total_points=500)

        categories = {}
        for key, name in CATEGORY_MAP.items():
            cat = Category(restaurant_id=restaurant.id, name=name, sort_order=len(categories))
            db.session.add(cat)
            db.session.flush()
            categories[key] = cat

        for i, (name, desc, price, is_veg, cat_key) in enumerate(SAMPLE_FOODS):
            food = FoodItem(
                restaurant_id=restaurant.id,
                category_id=categories[cat_key].id,
                name=name, description=desc, price=price, is_veg=is_veg,
                is_bestseller=i < 3, is_special=i == 0,
                preparation_time=15 + (i % 3) * 5,
            )
            db.session.add(food)
            db.session.flush()
            for size, adj in [('Small', -30), ('Medium', 0), ('Large', 50)]:
                db.session.add(FoodVariant(
                    food_item_id=food.id, name=size,
                    price_adjustment=adj, is_default=(size == 'Medium'),
                ))
            for addon, ap in [('Extra Cheese', 40), ('Extra Sauce', 20)]:
                db.session.add(FoodAddon(food_item_id=food.id, name=addon, price=ap))

        for cap, ttype in [(2, '2_seater'), (4, '4_seater'), (4, '4_seater'),
                           (6, '6_seater'), (8, '8_seater')]:
            table = Table(
                branch_id=branch.id,
                table_number=f'T{cap}-{Table.query.count() + 1}',
                capacity=cap, table_type=ttype,
            )
            table.generate_qr_code()
            db.session.add(table)

        for q, a in [
            ('How do I book a table?', 'Go to Bookings and select date, time, and guests.'),
            ('What payment methods are accepted?', 'UPI, cards, net banking, wallets, and cash.'),
            ('How does the loyalty program work?', 'Earn 1 point per rupee spent. Silver, Gold, Platinum tiers.'),
        ]:
            db.session.add(FAQ(question=q, answer=a, restaurant_id=restaurant.id))

        db.session.commit()
        print('Database seeded successfully!')
        print('Login credentials:')
        print('  Super Admin: superadmin@restaurantpro.com / Admin@123')
        print('  Admin:       admin@restaurantpro.com / Admin@123')
        print('  Customer:    customer@restaurantpro.com / Customer@123')
        print('  Staff:       chef@restaurantpro.com / Staff@123')


if __name__ == '__main__':
    seed()
