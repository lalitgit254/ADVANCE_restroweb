from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.routes.api import api_bp
from app.models.table import Booking
from app.services.booking_service import BookingService


@api_bp.route('/bookings/availability', methods=['GET'])
def api_table_availability():
    """Check table availability
    ---
    tags:
      - Bookings
    parameters:
      - name: branch_id
        in: query
        type: integer
        required: true
      - name: date
        in: query
        type: string
        required: true
      - name: time
        in: query
        type: string
        required: true
      - name: guests
        in: query
        type: integer
        required: true
    """
    branch_id = request.args.get('branch_id', type=int)
    booking_date = datetime.strptime(request.args.get('date'), '%Y-%m-%d').date()
    booking_time = datetime.strptime(request.args.get('time'), '%H:%M').time()
    guests = request.args.get('guests', type=int)

    tables = BookingService.get_available_tables(branch_id, booking_date, booking_time, guests)
    return jsonify([t.to_dict() for t in tables])


@api_bp.route('/bookings', methods=['POST'])
@jwt_required()
def api_create_booking():
    """Create a table booking
    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    try:
        booking = BookingService.create_booking(
            user_id,
            data['branch_id'],
            datetime.strptime(data['booking_date'], '%Y-%m-%d').date(),
            datetime.strptime(data['booking_time'], '%H:%M').time(),
            data['guests'],
            table_id=data.get('table_id'),
            special_requests=data.get('special_requests'),
        )
        return jsonify(booking.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/bookings', methods=['GET'])
@jwt_required()
def api_list_bookings():
    """List user's bookings
    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    bookings = Booking.query.filter_by(customer_id=user_id).order_by(Booking.booking_date.desc()).all()
    return jsonify([b.to_dict() for b in bookings])


@api_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def api_cancel_booking(booking_id):
    """Cancel a booking
    ---
    tags:
      - Bookings
    security:
      - Bearer: []
    """
    user_id = int(get_jwt_identity())
    try:
        booking = BookingService.cancel_booking(booking_id, user_id)
        return jsonify(booking.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400
