from flask import jsonify


def success_response(data=None, message: str = "Success", status_code: int = 200):
    return jsonify({"success": True, "message": message, "data": data}), status_code


def error_response(message: str = "Error", status_code: int = 400, errors=None):
    body = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


def paginated_response(items, pagination, message: str = "Success"):
    return jsonify({
        "success": True,
        "message": message,
        "data": items,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        }
    }), 200


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return error_response(str(e.description), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("Unauthorized", 401)

    @app.errorhandler(403)
    def forbidden(e):
        return error_response("Forbidden", 403)

    @app.errorhandler(404)
    def not_found(e):
        from flask import request
        if request.path.startswith("/api/"):
            return error_response("Resource not found", 404)
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def rate_limited(e):
        return error_response("Too many requests. Please slow down.", 429)

    @app.errorhandler(500)
    def server_error(e):
        return error_response("Internal server error", 500)
