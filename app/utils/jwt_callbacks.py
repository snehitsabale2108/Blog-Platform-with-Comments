from ..models.token_blocklist import TokenBlocklist
from ..extensions import db


def register_jwt_callbacks(jwt):
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return TokenBlocklist.query.filter_by(jti=jti).first() is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        from .errors import error_response
        return error_response("Token has been revoked", 401)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from .errors import error_response
        return error_response("Token has expired", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from .errors import error_response
        return error_response("Invalid token", 422)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from .errors import error_response
        return error_response("Authorization token is missing", 401)
