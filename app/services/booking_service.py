from datetime import datetime, timezone, timedelta, date, time
from flask import current_app
from app.extensions import db
from app.models.table import Table, Booking, WaitingList
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService


class BookingService:
    @staticmethod
    def get_available_tables(branch_id, booking_date, booking_time, guests):
        booked_table_ids = db.session.query(Booking.table_id).filter(
            Booking.branch_id == branch_id,
            Booking.booking_date == booking_date,
            Booking.booking_time == booking_time,
            Booking.status.in_(['pending', 'confirmed']),
            Booking.table_id.isnot(None),
        ).all()
        booked_ids = [t[0] for t in booked_table_ids]

        query = Table.query.filter(
            Table.branch_id == branch_id,
            Table.is_active == True,
            Table.capacity >= guests,
            Table.status == 'available',
        )
        if booked_ids:
            query = query.filter(Table.id.notin_(booked_ids))

        return query.order_by(Table.capacity).all()

    @staticmethod
    def create_booking(customer_id, branch_id, booking_date, booking_time,
                       guests, table_id=None, special_requests=None):
        advance_days = current_app.config.get('BOOKING_ADVANCE_DAYS', 30)
        max_date = date.today() + timedelta(days=advance_days)

        if booking_date > max_date:
            raise ValueError(f'Bookings can only be made up to {advance_days} days in advance')
        if booking_date < date.today():
            raise ValueError('Cannot book for past dates')

        if table_id:
            table = Table.query.get(table_id)
            if not table or table.capacity < guests:
                raise ValueError('Selected table is not suitable')

        booking = Booking(
            customer_id=customer_id,
            branch_id=branch_id,
            table_id=table_id,
            booking_date=booking_date,
            booking_time=booking_time,
            guests=guests,
            special_requests=special_requests,
            expires_at=datetime.combine(booking_date, booking_time) + timedelta(hours=2),
        )
        booking.generate_codes()
        db.session.add(booking)

        if table_id:
            table = Table.query.get(table_id)
            table.status = 'reserved'

        db.session.commit()

        from app.models.user import User
        user = User.query.get(customer_id)
        if user:
            NotificationService.notify_booking_update(booking, user)
            EmailService.send_booking_confirmation(booking, user)

        return booking

    @staticmethod
    def cancel_booking(booking_id, customer_id=None):
        booking = Booking.query.get_or_404(booking_id)
        if customer_id and booking.customer_id != customer_id:
            raise PermissionError('Not authorized')

        booking.status = 'cancelled'
        if booking.table_id:
            table = Table.query.get(booking.table_id)
            if table:
                table.status = 'available'

        db.session.commit()
        return booking

    @staticmethod
    def reschedule_booking(booking_id, new_date, new_time, customer_id=None):
        booking = Booking.query.get_or_404(booking_id)
        if customer_id and booking.customer_id != customer_id:
            raise PermissionError('Not authorized')

        if booking.table_id:
            old_table = Table.query.get(booking.table_id)
            if old_table:
                old_table.status = 'available'

        booking.booking_date = new_date
        booking.booking_time = new_time
        booking.status = 'pending'
        booking.table_id = None
        db.session.commit()
        return booking

    @staticmethod
    def expire_unused_bookings():
        now = datetime.now(timezone.utc)
        expired = Booking.query.filter(
            Booking.status.in_(['pending', 'confirmed']),
            Booking.expires_at < now,
        ).all()

        for booking in expired:
            booking.status = 'expired'
            if booking.table_id:
                table = Table.query.get(booking.table_id)
                if table:
                    table.status = 'available'

        db.session.commit()
        return len(expired)

    @staticmethod
    def add_to_waiting_list(customer_id, branch_id, guests, preferred_table_type=None):
        position = WaitingList.query.filter_by(
            branch_id=branch_id, status='waiting'
        ).count() + 1

        entry = WaitingList(
            customer_id=customer_id,
            branch_id=branch_id,
            guests=guests,
            preferred_table_type=preferred_table_type,
            position=position,
        )
        db.session.add(entry)
        db.session.commit()
        return entry
