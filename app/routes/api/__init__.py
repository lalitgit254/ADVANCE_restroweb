from flask import Blueprint
from flasgger import Swagger

api_bp = Blueprint('api', __name__)

swagger_config = {
    'headers': [],
    'specs': [{
        'endpoint': 'apispec',
        'route': '/apispec.json',
        'rule_filter': lambda rule: True,
        'model_filter': lambda tag: True,
    }],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/docs',
}

swagger_template = {
    'info': {
        'title': 'RestaurantPro API',
        'description': 'Enterprise Restaurant Management REST API',
        'version': '1.0.0',
    },
    'securityDefinitions': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header. Example: Bearer <token>',
        }
    },
}

from app.routes.api import auth, menu, orders, bookings, payments  # noqa: E402, F401
