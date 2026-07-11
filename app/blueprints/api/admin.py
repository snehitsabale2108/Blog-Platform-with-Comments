from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ...extensions import db
from ...models.user import User
from ...models import Post, Comment, Category, Tag
from ...utils.errors import success_response, error_response, paginated_response

api_admin_bp = Blueprint("api_admin", __name__)


def require_admin():
    from flask_jwt_extended import get_jwt_identity
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != "admin":
        return None, error_response("Admin access required", 403)
    return user, None


@api_admin_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    _, err = require_admin()
    if err:
        return err
    from ...models.like import Like
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    stats = {
        "total_users": User.query.count(),
        "new_users_week": User.query.filter(User.created_at >= week_ago).count(),
        "total_posts": Post.query.filter_by(status="published").count(),
        "new_posts_week": Post.query.filter(Post.published_at >= week_ago, Post.status == "published").count(),
        "total_comments": Comment.query.count(),
        "total_likes": Like.query.count(),
        "flagged_posts": Post.query.filter_by(status="flagged").count(),
        "flagged_comments": Comment.query.filter_by(is_flagged=True).count(),
    }
    return success_response(stats)


@api_admin_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    _, err = require_admin()
    if err:
        return err
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    q = request.args.get("q", "")
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response([u.to_dict(include_email=True) for u in pagination.items], pagination)


@api_admin_bp.route("/users/<int:user_id>/block", methods=["POST"])
@jwt_required()
def toggle_block(user_id):
    admin, err = require_admin()
    if err:
        return err
    user = User.query.get_or_404(user_id)
    if user.id == admin.id:
        return error_response("Cannot block yourself", 400)
    user.is_active = not user.is_active
    db.session.commit()
    return success_response({"is_active": user.is_active})


@api_admin_bp.route("/posts/<int:post_id>/flag", methods=["POST"])
@jwt_required()
def flag_post(post_id):
    _, err = require_admin()
    if err:
        return err
    post = Post.query.get_or_404(post_id)
    post.status = "flagged"
    db.session.commit()
    return success_response(message="Post flagged")


@api_admin_bp.route("/posts/<int:post_id>/approve", methods=["POST"])
@jwt_required()
def approve_post(post_id):
    _, err = require_admin()
    if err:
        return err
    post = Post.query.get_or_404(post_id)
    post.status = "published"
    db.session.commit()
    return success_response(message="Post approved")


@api_admin_bp.route("/categories", methods=["GET"])
def list_categories():
    cats = Category.query.all()
    return success_response([c.to_dict() for c in cats])


@api_admin_bp.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    _, err = require_admin()
    if err:
        return err
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return error_response("Name required", 422)
    from slugify import slugify
    cat = Category(
        name=name,
        slug=slugify(name),
        description=data.get("description", ""),
        color=data.get("color", "#3b82d4"),
        icon=data.get("icon", "bi-journal"),
    )
    db.session.add(cat)
    db.session.commit()
    return success_response(cat.to_dict(), "Category created", 201)


@api_admin_bp.route("/tags", methods=["GET"])
def list_tags():
    tags = Tag.query.all()
    return success_response([t.to_dict() for t in tags])
