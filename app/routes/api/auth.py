from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.routes.api import api_bp
from app.services.auth_service import AuthService
from app.models.user import User


@api_bp.route('/auth/register', methods=['POST'])
def api_register():
    """Register a new customer account
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [email, password, first_name, last_name]
          properties:
            email: {type: string}
            password: {type: string}
            first_name: {type: string}
            last_name: {type: string}
            phone: {type: string}
    responses:
      201:
        description: User created
    """
    data = request.get_json()
    try:
        user = AuthService.register(
            data['email'], data['password'],
            data['first_name'], data['last_name'],
            data.get('phone'), data.get('referral_code')
        )
        return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Login and receive JWT tokens
    ---
    tags:
      - Auth
    """
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'user': user.to_dict(),
    })


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def api_me():
    """Get current user profile
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    """
    user = User.query.get(int(get_jwt_identity()))
    return jsonify(user.to_dict())


@api_bp.route('/auth/otp/send', methods=['POST'])
def api_send_otp():
    """Send OTP for login
    ---
    tags:
      - Auth
    """
    data = request.get_json()
    AuthService.send_otp(email=data.get('email'), phone=data.get('phone'))
    return jsonify({'message': 'OTP sent'})


@api_bp.route('/auth/otp/verify', methods=['POST'])
def api_verify_otp():
    """Verify OTP and receive JWT tokens
    ---
    tags:
      - Auth
    """
    data = request.get_json()
    try:
        user = AuthService.verify_otp(data['email'], data['otp'])
        access = create_access_token(identity=str(user.id))
        refresh = create_refresh_token(identity=str(user.id))
        return jsonify({'access_token': access, 'refresh_token': refresh, 'user': user.to_dict()})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
