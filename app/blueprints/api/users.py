from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from ...extensions import db
from ...models.user import User
from ...models import Post, Bookmark
from ...utils.errors import success_response, error_response, paginated_response
from ...utils.image_handler import save_image

api_users_bp = Blueprint("api_users", __name__)


def optional_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        return User.query.get(uid) if uid else None
    except Exception:
        return None


@api_users_bp.route("/<username>", methods=["GET"])
def get_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user = optional_user()
    data = user.to_dict()
    if current_user:
        data["is_following"] = current_user.is_following(user)
    return success_response(data)


@api_users_bp.route("/<username>/posts", methods=["GET"])
def get_user_posts(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 50)
    pagination = user.posts.filter_by(status="published")\
        .order_by(Post.published_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    items = [p.to_dict() for p in pagination.items]
    return paginated_response(items, pagination)


@api_users_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json() or {}
    for field in ("display_name", "bio", "website", "twitter", "github", "linkedin"):
        if field in data:
            setattr(user, field, data[field].strip() if data[field] else None)

    db.session.commit()
    return success_response(user.to_dict(include_email=True), "Profile updated")


@api_users_bp.route("/<username>/follow", methods=["POST"])
@jwt_required()
def follow_user(username):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    target = User.query.filter_by(username=username).first_or_404()

    if current_user.id == target.id:
        return error_response("Cannot follow yourself", 400)

    if current_user.is_following(target):
        current_user.unfollow(target)
        following = False
    else:
        current_user.follow(target)
        following = True
    db.session.commit()
    return success_response({
        "following": following,
        "follower_count": target.follower_count,
    })


@api_users_bp.route("/me/bookmarks", methods=["GET"])
@jwt_required()
def get_bookmarks():
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 50)
    pagination = Bookmark.query.filter_by(user_id=user_id)\
        .order_by(Bookmark.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    items = [b.post.to_dict() for b in pagination.items if b.post]
    return paginated_response(items, pagination)


@api_users_bp.route("/me/feed", methods=["GET"])
@jwt_required()
def get_feed():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 50)
    followed_ids = [u.id for u in user.followed.all()]
    pagination = Post.query.filter(
        Post.author_id.in_(followed_ids),
        Post.status == "published"
    ).order_by(Post.published_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    items = [p.to_dict(current_user=user) for p in pagination.items]
    return paginated_response(items, pagination)


@api_users_bp.route("/me/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    from ...models.notification import Notification
    user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(user_id=user_id)\
        .order_by(Notification.created_at.desc()).limit(30).all()
    return success_response([n.to_dict() for n in notifications])


@api_users_bp.route("/me/notifications/read", methods=["POST"])
@jwt_required()
def mark_notifications_read():
    from ...models.notification import Notification
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return success_response(message="Notifications marked as read")
