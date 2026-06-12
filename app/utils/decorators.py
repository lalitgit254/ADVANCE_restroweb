from functools import wraps
from flask import jsonify, redirect, url_for, flash, request
from flask_login import current_user


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('auth.login'))
            if current_user.role not in roles and 'super_admin' not in (current_user.role,):
                if current_user.role == 'super_admin':
                    return f(*args, **kwargs)
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('super_admin', 'admin', 'manager')(f)


def staff_required(f):
    return role_required('super_admin', 'admin', 'manager', 'chef', 'waiter', 'cashier', 'delivery_boy')(f)
