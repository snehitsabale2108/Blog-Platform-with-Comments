from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from ...extensions import db
from ...models import Post, Category, Tag, Like, Bookmark
from ...models.user import User
from ...utils.errors import success_response, error_response, paginated_response
from datetime import datetime

api_posts_bp = Blueprint("api_posts", __name__)


def optional_user():
    try:
        verify_jwt_in_request(optional=True)
        uid = get_jwt_identity()
        return User.query.get(uid) if uid else None
    except Exception:
        return None


@api_posts_bp.route("/", methods=["GET"])
def list_posts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 12, type=int), 50)
    q = request.args.get("q", "")
    category = request.args.get("category", "")
    tag = request.args.get("tag", "")
    sort = request.args.get("sort", "latest")
    author = request.args.get("author", "")

    query = Post.query.filter_by(status="published")
    if q:
        query = query.filter(Post.title.ilike(f"%{q}%") | Post.excerpt.ilike(f"%{q}%"))
    if category:
        cat = Category.query.filter_by(slug=category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if tag:
        t = Tag.query.filter_by(slug=tag).first()
        if t:
            query = query.filter(Post.tags.contains(t))
    if author:
        u = User.query.filter_by(username=author).first()
        if u:
            query = query.filter_by(author_id=u.id)
    if sort == "popular":
        query = query.order_by(Post.view_count.desc())
    elif sort == "trending":
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.published_at >= week_ago).order_by(Post.view_count.desc())
    else:
        query = query.order_by(Post.published_at.desc())

    current_user = optional_user()
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = [p.to_dict(current_user=current_user) for p in pagination.items]
    return paginated_response(items, pagination)


@api_posts_bp.route("/<slug>", methods=["GET"])
def get_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user = optional_user()
    if post.status != "published":
        if not current_user or (current_user.id != post.author_id and current_user.role != "admin"):
            return error_response("Post not found", 404)
    post.increment_views()
    db.session.commit()
    return success_response(post.to_dict(include_content=True, current_user=current_user))


@api_posts_bp.route("/", methods=["POST"])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json() or {}
    title = data.get("title", "").strip()
    content = data.get("content", "")
    if not title or not content:
        return error_response("Title and content are required", 422)

    post = Post(
        title=title,
        content=content,
        excerpt=data.get("excerpt", content[:300]),
        author_id=user_id,
        category_id=data.get("category_id"),
    )
    post.generate_slug()
    post.calculate_reading_time()

    tag_ids = data.get("tag_ids", [])
    if tag_ids:
        post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

    action = data.get("action", "draft")
    if action == "publish":
        post.status = "published"
        post.published_at = datetime.utcnow()

    db.session.add(post)
    db.session.commit()
    return success_response(post.to_dict(include_content=True), "Post created", 201)


@api_posts_bp.route("/<slug>", methods=["PUT", "PATCH"])
@jwt_required()
def update_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or (user.id != post.author_id and user.role != "admin"):
        return error_response("Forbidden", 403)

    data = request.get_json() or {}
    if "title" in data:
        post.title = data["title"].strip()
    if "content" in data:
        post.content = data["content"]
        post.calculate_reading_time()
    if "excerpt" in data:
        post.excerpt = data["excerpt"][:500]
    if "category_id" in data:
        post.category_id = data["category_id"]
    if "tag_ids" in data:
        post.tags = Tag.query.filter(Tag.id.in_(data["tag_ids"])).all()
    if "action" in data:
        if data["action"] == "publish" and post.status != "published":
            post.status = "published"
            post.published_at = datetime.utcnow()
        elif data["action"] == "draft":
            post.status = "draft"

    db.session.commit()
    return success_response(post.to_dict(include_content=True), "Post updated")


@api_posts_bp.route("/<slug>", methods=["DELETE"])
@jwt_required()
def delete_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or (user.id != post.author_id and user.role != "admin"):
        return error_response("Forbidden", 403)
    db.session.delete(post)
    db.session.commit()
    return success_response(message="Post deleted")


@api_posts_bp.route("/<slug>/like", methods=["POST"])
@jwt_required()
def toggle_like(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    user_id = get_jwt_identity()
    existing = Like.query.filter_by(user_id=user_id, target_type="post", target_id=post.id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=user_id, target_type="post", target_id=post.id))
        liked = True
    db.session.commit()
    return success_response({"liked": liked, "count": post.like_count})


@api_posts_bp.route("/<slug>/bookmark", methods=["POST"])
@jwt_required()
def toggle_bookmark(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    user_id = get_jwt_identity()
    existing = Bookmark.query.filter_by(user_id=user_id, post_id=post.id).first()
    if existing:
        db.session.delete(existing)
        bookmarked = False
    else:
        db.session.add(Bookmark(user_id=user_id, post_id=post.id))
        bookmarked = True
    db.session.commit()
    return success_response({"bookmarked": bookmarked})
