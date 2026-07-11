from flask import Blueprint, render_template, session
from ...models import Post, Category, Tag
from ...models.user import User

main_bp = Blueprint("main", __name__)


def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@main_bp.route("/")
def index():
    featured = Post.query.filter_by(status="published", is_featured=True)\
        .order_by(Post.published_at.desc()).limit(1).first()
    latest = Post.query.filter_by(status="published")\
        .order_by(Post.published_at.desc()).limit(9).all()
    categories = Category.query.all()
    popular = Post.query.filter_by(status="published")\
        .order_by(Post.view_count.desc()).limit(5).all()
    return render_template(
        "main/index.html",
        featured=featured,
        latest=latest,
        categories=categories,
        popular=popular,
        current_user=get_current_user(),
    )
