import io
import base64
import qrcode
from flask import current_app


def generate_qr_base64(data, size=10):
    qr = qrcode.QRCode(version=1, box_size=size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def generate_table_qr_url(table_qr_code):
    base_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    return f'{base_url}/menu/qr/{table_qr_code}'


def generate_booking_qr_url(booking_qr_code):
    base_url = current_app.config.get('APP_URL', 'http://localhost:5000')
    return f'{base_url}/booking/verify/{booking_qr_code}'
