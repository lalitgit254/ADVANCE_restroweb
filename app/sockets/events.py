from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app.extensions import socketio


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        if current_user.restaurant_id:
            join_room(f'restaurant_{current_user.restaurant_id}')
        if current_user.branch_id:
            join_room(f'branch_{current_user.branch_id}_kitchen')
            if current_user.role == 'waiter':
                join_room(f'branch_{current_user.branch_id}_waiters')
            if current_user.role == 'delivery_boy':
                join_room(f'branch_{current_user.branch_id}_delivery')
        emit('connected', {'user_id': current_user.id, 'role': current_user.role})
    else:
        emit('connected', {'anonymous': True})


@socketio.on('disconnect')
def handle_disconnect():
    pass


@socketio.on('join_order')
def join_order(data):
    order_id = data.get('order_id')
    if order_id:
        join_room(f'order_{order_id}')
        emit('joined', {'room': f'order_{order_id}'})


@socketio.on('leave_order')
def leave_order(data):
    order_id = data.get('order_id')
    if order_id:
        leave_room(f'order_{order_id}')


@socketio.on('join_branch')
def join_branch(data):
    branch_id = data.get('branch_id')
    role = data.get('role', 'kitchen')
    if branch_id:
        room = f'branch_{branch_id}_{role}'
        join_room(room)
        emit('joined', {'room': room})


@socketio.on('call_waiter')
def handle_call_waiter(data):
    table_id = data.get('table_id')
    branch_id = data.get('branch_id')
    table_number = data.get('table_number')
    if branch_id:
        emit('call_waiter', {
            'table_id': table_id,
            'table_number': table_number,
            'type': 'call_waiter',
        }, room=f'branch_{branch_id}_waiters', include_self=False)


@socketio.on('chat_message')
def handle_chat_message(data):
    ticket_id = data.get('ticket_id')
    message = data.get('message')
    if ticket_id and message:
        emit('chat_message', {
            'ticket_id': ticket_id,
            'message': message,
            'sender_id': current_user.id if current_user.is_authenticated else None,
        }, room=f'ticket_{ticket_id}')


@socketio.on('join_ticket')
def join_ticket(data):
    ticket_id = data.get('ticket_id')
    if ticket_id:
        join_room(f'ticket_{ticket_id}')


@socketio.on('delivery_location')
def handle_delivery_location(data):
    order_id = data.get('order_id')
    lat = data.get('latitude')
    lng = data.get('longitude')
    if order_id:
        emit('delivery_location', {
            'order_id': order_id,
            'latitude': lat,
            'longitude': lng,
        }, room=f'order_{order_id}', include_self=False)
