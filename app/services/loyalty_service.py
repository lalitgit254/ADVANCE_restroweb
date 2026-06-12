from flask import current_app
from app.extensions import db
from app.models.loyalty import LoyaltyPoint, LoyaltyTransaction


class LoyaltyService:
    @staticmethod
    def get_or_create(user_id, restaurant_id=None):
        loyalty = LoyaltyPoint.query.filter_by(user_id=user_id).first()
        if not loyalty:
            loyalty = LoyaltyPoint(user_id=user_id, restaurant_id=restaurant_id)
            db.session.add(loyalty)
            db.session.flush()
        return loyalty

    @staticmethod
    def earn_points(user_id, order_id, amount):
        points_per_rupee = current_app.config.get('LOYALTY_POINTS_PER_RUPEE', 1)
        points = int(float(amount) * points_per_rupee)
        loyalty = LoyaltyService.get_or_create(user_id)

        loyalty.total_points += points
        loyalty.lifetime_points += points
        loyalty.update_level()

        transaction = LoyaltyTransaction(
            loyalty_id=loyalty.id,
            order_id=order_id,
            points=points,
            transaction_type='earn',
            description=f'Earned {points} points from order',
        )
        db.session.add(transaction)
        return points

    @staticmethod
    def redeem_points(user_id, points, order_id=None):
        loyalty = LoyaltyService.get_or_create(user_id)
        if loyalty.total_points < points:
            return False

        loyalty.total_points -= points
        transaction = LoyaltyTransaction(
            loyalty_id=loyalty.id,
            order_id=order_id,
            points=-points,
            transaction_type='redeem',
            description=f'Redeemed {points} points',
        )
        db.session.add(transaction)
        return True

    @staticmethod
    def referral_reward(referrer_id, referred_id):
        loyalty = LoyaltyService.get_or_create(referrer_id)
        bonus_points = 100
        loyalty.total_points += bonus_points
        loyalty.lifetime_points += bonus_points
        loyalty.referral_count += 1
        loyalty.update_level()

        transaction = LoyaltyTransaction(
            loyalty_id=loyalty.id,
            points=bonus_points,
            transaction_type='referral',
            description='Referral bonus',
        )
        db.session.add(transaction)

    @staticmethod
    def get_membership_discount(level):
        discounts = {'silver': 0, 'gold': 5, 'platinum': 10}
        return discounts.get(level, 0)
