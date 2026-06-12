import secrets
import re
from datetime import datetime, timezone, timedelta
from flask import request, current_app
import bleach


def generate_referral_code():
    return secrets.token_hex(4).upper()


def generate_otp(length=6):
    return ''.join([str(secrets.randbelow(10)) for _ in range(length)])


def sanitize_html(text):
    if not text:
        return text
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    return bleach.clean(text, tags=allowed_tags, strip=True)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    pattern = r'^\+?[\d\s-]{10,15}$'
    return re.match(pattern, phone) is not None


def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def paginate_query(query, page=1, per_page=20):
    return query.paginate(page=page, per_page=per_page, error_out=False)


def calculate_gst(amount, rate=5):
    return round(float(amount) * rate / 100, 2)


def get_dashboard_url(role):
    routes = {
        'super_admin': 'super_admin.dashboard',
        'admin': 'admin.dashboard',
        'manager': 'admin.dashboard',
        'chef': 'chef.dashboard',
        'waiter': 'waiter.dashboard',
        'cashier': 'cashier.dashboard',
        'delivery_boy': 'delivery.dashboard',
        'customer': 'customer.dashboard',
    }
    return routes.get(role, 'main.index')


def utcnow():
    return datetime.now(timezone.utc)


def add_days(dt, days):
    return dt + timedelta(days=days)
