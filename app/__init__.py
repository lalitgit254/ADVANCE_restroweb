import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from app.config import config
from app.extensions import db, migrate, login_manager, jwt, socketio, limiter, cors

csrf = CSRFProtect()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    flask_app = Flask(__name__,
                      template_folder='../templates',
                      static_folder='../static')
    flask_app.config.from_object(config[config_name])

    os.makedirs(flask_app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    jwt.init_app(flask_app)
    limiter.init_app(flask_app)
    csrf.init_app(flask_app)
    cors.init_app(flask_app, resources={r'/api/*': {'origins': '*'}})
    socketio.init_app(flask_app)

    from app.models import user as user_model

    @login_manager.user_loader
    def load_user(user_id):
        return user_model.User.query.get(int(user_id))

    register_blueprints(flask_app)
    csrf.exempt(flask_app.blueprints.get('api'))
    register_error_handlers(flask_app)
    register_context_processors(flask_app)

    import app.sockets.events  # noqa: F401

    return flask_app


def register_blueprints(app):
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.customer import customer_bp
    from app.routes.admin import admin_bp
    from app.routes.super_admin import super_admin_bp
    from app.routes.chef import chef_bp
    from app.routes.waiter import waiter_bp
    from app.routes.cashier import cashier_bp
    from app.routes.delivery import delivery_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(super_admin_bp, url_prefix='/super-admin')
    app.register_blueprint(chef_bp, url_prefix='/chef')
    app.register_blueprint(waiter_bp, url_prefix='/waiter')
    app.register_blueprint(cashier_bp, url_prefix='/cashier')
    app.register_blueprint(delivery_bp, url_prefix='/delivery')
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    from flask import render_template, jsonify, request

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def register_context_processors(app):
    from flask_login import current_user

    @app.context_processor
    def inject_globals():
        return {
            'app_name': app.config['APP_NAME'],
            'current_year': 2026,
        }
