from functools import wraps
from flask import abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from ..models.user import User


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request(optional=True)
        from flask_jwt_extended import get_jwt_identity
        from flask import session
        user_id = get_jwt_identity() or session.get("user_id")
        if not user_id:
            abort(401)
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request(optional=True)
            from flask import session
            user_id = get_jwt_identity() or session.get("user_id")
            if not user_id:
                abort(401)
            user = User.query.get(user_id)
            if not user or user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return roles_required("admin")(fn)
