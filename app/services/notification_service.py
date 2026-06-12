from app.extensions import db, socketio
from app.models.notification import Notification
from app.services.email_service import EmailService


class NotificationService:
    @staticmethod
    def create(user_id, title, message, notification_type, channel='in_app',
               reference_type=None, reference_id=None):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        db.session.add(notification)
        db.session.flush()

        if channel in ('in_app', 'push'):
            socketio.emit('notification', notification.to_dict(), room=f'user_{user_id}')

        return notification

    @staticmethod
    def notify_order_update(order):
        title = f'Order {order.order_number} Updated'
        message = f'Your order status is now: {order.status.replace("_", " ").title()}'
        NotificationService.create(
            order.customer_id, title, message, 'order_update',
            reference_type='order', reference_id=order.id
        )
        socketio.emit('order_update', order.to_dict(), room=f'order_{order.id}')
        socketio.emit('order_update', order.to_dict(), room=f'restaurant_{order.restaurant_id}')

    @staticmethod
    def notify_booking_update(booking, user):
        title = 'Booking Update'
        message = f'Your booking status: {booking.status.replace("_", " ").title()}'
        NotificationService.create(
            user.id, title, message, 'booking_update',
            reference_type='booking', reference_id=booking.id
        )

    @staticmethod
    def notify_staff(room, event, data):
        socketio.emit(event, data, room=room)

    @staticmethod
    def call_waiter(table_id, branch_id, table_number):
        data = {'table_id': table_id, 'table_number': table_number, 'type': 'call_waiter'}
        socketio.emit('call_waiter', data, room=f'branch_{branch_id}_waiters')

    @staticmethod
    def mark_read(notification_id, user_id):
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
        return notification

    @staticmethod
    def mark_all_read(user_id):
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
