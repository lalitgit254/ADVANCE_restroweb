from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins='*', async_mode='threading')
limiter = Limiter(key_func=get_remote_address, default_limits=['200 per minute'])
cors = CORS()

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'
