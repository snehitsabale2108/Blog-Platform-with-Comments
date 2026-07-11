from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from ...extensions import db
from ...models.user import User
from ...models.token_blocklist import TokenBlocklist
from ...utils.errors import success_response, error_response
from ...utils.email import send_verification_email, send_password_reset_email
from datetime import datetime

api_auth_bp = Blueprint("api_auth", __name__)


@api_auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    display_name = data.get("display_name", "").strip()

    errors = {}
    if not username or len(username) < 3:
        errors["username"] = "Username must be at least 3 characters."
    if not email or "@" not in email:
        errors["email"] = "A valid email is required."
    if not password or len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    if errors:
        return error_response("Validation failed", 422, errors)

    if User.query.filter_by(username=username).first():
        return error_response("Username already taken", 409)
    if User.query.filter_by(email=email).first():
        return error_response("Email already registered", 409)

    user = User(username=username, email=email, display_name=display_name or username, role="author")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    send_verification_email(user)
    return success_response(user.to_dict(include_email=True), "Registration successful. Please verify your email.", 201)


@api_auth_bp.route("/login", methods=["POST"])
def login():
    from ...extensions import limiter
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")

    user = (
        User.query.filter_by(email=identifier).first()
        or User.query.filter_by(username=identifier).first()
    )
    if not user or not user.check_password(password):
        return error_response("Invalid credentials", 401)
    if not user.is_active:
        return error_response("Account suspended", 403)

    user.last_seen = datetime.utcnow()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return success_response({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(include_email=True),
    }, "Login successful")


@api_auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return success_response({"access_token": access_token}, "Token refreshed")


@api_auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    db.session.add(TokenBlocklist(jti=jti, created_at=datetime.utcnow()))
    db.session.commit()
    return success_response(message="Logged out successfully")


@api_auth_bp.route("/verify/<token>", methods=["GET"])
def verify_email(token):
    user = User.verify_token(token, salt="email-confirm")
    if not user:
        return error_response("Invalid or expired token", 400)
    user.is_email_verified = True
    db.session.commit()
    return success_response(message="Email verified")


@api_auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user:
        send_password_reset_email(user)
    return success_response(message="If that email exists, a reset link has been sent")


@api_auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json() or {}
    token = data.get("token", "")
    password = data.get("password", "")
    user = User.verify_token(token, salt="password-reset")
    if not user:
        return error_response("Invalid or expired token", 400)
    if len(password) < 8:
        return error_response("Password must be at least 8 characters", 422)
    user.set_password(password)
    db.session.commit()
    return success_response(message="Password reset successful")


@api_auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict(include_email=True))
