from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from ...extensions import db
from ...models import Comment, Post, Like
from ...models.user import User
from ...utils.errors import success_response, error_response, paginated_response

api_comments_bp = Blueprint("api_comments", __name__)


def optional_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        return User.query.get(uid) if uid else None
    except Exception:
        return None


@api_comments_bp.route("/post/<int:post_id>", methods=["GET"])
def get_comments(post_id):
    post = Post.query.get_or_404(post_id)
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    current_user = optional_user()
    pagination = post.comments.filter_by(parent_id=None, is_approved=True)\
        .order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    items = [c.to_dict(current_user=current_user, include_replies=True) for c in pagination.items]
    return paginated_response(items, pagination)


@api_comments_bp.route("/post/<int:post_id>", methods=["POST"])
@jwt_required()
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    parent_id = data.get("parent_id")

    if not content or len(content) < 2:
        return error_response("Comment content is required", 422)

    comment = Comment(
        content=content,
        post_id=post_id,
        author_id=user_id,
        parent_id=parent_id,
    )
    db.session.add(comment)
    db.session.commit()
    return success_response(comment.to_dict(), "Comment added", 201)


@api_comments_bp.route("/<int:comment_id>", methods=["PUT"])
@jwt_required()
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = get_jwt_identity()
    if comment.author_id != user_id:
        return error_response("Forbidden", 403)
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return error_response("Content cannot be empty", 422)
    comment.content = content
    db.session.commit()
    return success_response(comment.to_dict(), "Comment updated")


@api_comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if comment.author_id != user_id and (not user or user.role != "admin"):
        return error_response("Forbidden", 403)
    db.session.delete(comment)
    db.session.commit()
    return success_response(message="Comment deleted")


@api_comments_bp.route("/<int:comment_id>/like", methods=["POST"])
@jwt_required()
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = get_jwt_identity()
    existing = Like.query.filter_by(user_id=user_id, target_type="comment", target_id=comment_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=user_id, target_type="comment", target_id=comment_id))
        liked = True
    db.session.commit()
    return success_response({"liked": liked, "count": comment.like_count})


@api_comments_bp.route("/<int:comment_id>/flag", methods=["POST"])
@jwt_required()
def flag_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_flagged = True
    db.session.commit()
    return success_response(message="Comment flagged for review")
