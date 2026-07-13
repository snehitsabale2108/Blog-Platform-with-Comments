from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ...extensions import db
from ...models import Post, Category, Tag, Like, Bookmark
from ...models.user import User
from slugify import slugify
from datetime import datetime

posts_bp = Blueprint("posts", __name__, template_folder="../../templates/posts")


def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@posts_bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    category = request.args.get("category", "")
    tag = request.args.get("tag", "")
    sort = request.args.get("sort", "latest")

    query = Post.query.filter_by(status="published")

    if q:
        query = query.filter(
            Post.title.ilike(f"%{q}%") | Post.content.ilike(f"%{q}%") | Post.excerpt.ilike(f"%{q}%")
        )
    if category:
        cat = Category.query.filter_by(slug=category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if tag:
        t = Tag.query.filter_by(slug=tag).first()
        if t:
            query = query.filter(Post.tags.contains(t))

    if sort == "popular":
        query = query.order_by(Post.view_count.desc())
    elif sort == "trending":
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(Post.published_at >= week_ago).order_by(Post.view_count.desc())
    else:
        query = query.order_by(Post.published_at.desc())

    from flask import current_app
    pagination = query.paginate(page=page, per_page=current_app.config["POSTS_PER_PAGE"], error_out=False)

    categories = Category.query.all()
    popular_tags = Tag.query.all()
    featured = Post.query.filter_by(status="published", is_featured=True).order_by(Post.published_at.desc()).limit(3).all()

    return render_template(
        "posts/index.html",
        posts=pagination.items,
        pagination=pagination,
        categories=categories,
        popular_tags=popular_tags,
        featured=featured,
        current_q=q,
        current_category=category,
        current_tag=tag,
        current_sort=sort,
        current_user=get_current_user(),
    )


@posts_bp.route("/<slug>")
def detail(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    if post.status != "published" and session.get("user_id") != post.author_id:
        if session.get("user_role") != "admin":
            from flask import abort
            abort(404)

    post.increment_views()
    db.session.commit()

    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)
    from flask import current_app
    comments_pagination = post.comments.filter_by(parent_id=None, is_approved=True)\
        .order_by(db.text("created_at DESC"))\
        .paginate(page=page, per_page=current_app.config["COMMENTS_PER_PAGE"], error_out=False)

    related = Post.query.filter(
        Post.category_id == post.category_id,
        Post.id != post.id,
        Post.status == "published"
    ).order_by(Post.published_at.desc()).limit(4).all()

    return render_template(
        "posts/detail.html",
        post=post,
        comments=comments_pagination.items,
        comments_pagination=comments_pagination,
        related=related,
        current_user=current_user,
    )


@posts_bp.route("/new", methods=["GET", "POST"])
def create():
    current_user = get_current_user()
    if not current_user:
        flash("Please log in.", "warning")
        return redirect(url_for("auth.login"))

    categories = Category.query.all()
    tags = Tag.query.all()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "")
        excerpt = request.form.get("excerpt", "").strip()
        category_id = request.form.get("category_id", type=int)
        tag_ids = request.form.getlist("tags", type=int)
        action = request.form.get("action", "draft")

        post = Post(
            title=title,
            content=content,
            excerpt=excerpt[:500] if excerpt else content[:300],
            author_id=current_user.id,
            category_id=category_id or None,
        )
        post.generate_slug()
        post.calculate_reading_time()

        if tag_ids:
            post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

        if current_user.role == "admin":
            is_featured_value = request.form.get("is_featured") == "1"
            if is_featured_value:
                Post.query.update({"is_featured": False})
            post.is_featured = is_featured_value

        cover = request.files.get("cover_image")
        if cover and cover.filename:
            from ...utils.image_handler import save_image
            saved = save_image(cover, "covers", (1200, 630))
            if saved:
                post.cover_image = saved

        if action == "publish":
            post.status = "published"
            post.published_at = datetime.utcnow()
        else:
            post.status = "draft"

        db.session.add(post)
        db.session.commit()
        flash("Post saved!", "success")
        return redirect(url_for("posts.detail", slug=post.slug))

    return render_template("posts/editor.html", post=None, categories=categories, tags=tags, current_user=current_user)


@posts_bp.route("/<slug>/edit", methods=["GET", "POST"])
def edit(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    if not current_user or (current_user.id != post.author_id and current_user.role != "admin"):
        flash("Permission denied.", "danger")
        return redirect(url_for("posts.detail", slug=slug))

    categories = Category.query.all()
    tags = Tag.query.all()

    if request.method == "POST":
        post.title = request.form.get("title", "").strip()
        post.content = request.form.get("content", "")
        post.excerpt = request.form.get("excerpt", "").strip()[:500]
        post.category_id = request.form.get("category_id", type=int) or None
        tag_ids = request.form.getlist("tags", type=int)
        action = request.form.get("action", "draft")

        post.calculate_reading_time()

        if tag_ids:
            post.tags = Tag.query.filter(Tag.id.in_(tag_ids)).all()

        if current_user.role == "admin":
            is_featured_value = request.form.get("is_featured") == "1"
            if is_featured_value:
                Post.query.filter(Post.id != post.id).update({"is_featured": False})
            post.is_featured = is_featured_value

        cover = request.files.get("cover_image")
        if cover and cover.filename:
            from ...utils.image_handler import save_image
            saved = save_image(cover, "covers", (1200, 630))
            if saved:
                post.cover_image = saved

        if action == "publish" and post.status != "published":
            post.status = "published"
            post.published_at = datetime.utcnow()
        elif action == "draft":
            post.status = "draft"

        db.session.commit()
        flash("Post updated!", "success")
        return redirect(url_for("posts.detail", slug=post.slug))

    return render_template("posts/editor.html", post=post, categories=categories, tags=tags, current_user=current_user)


@posts_bp.route("/<slug>/delete", methods=["POST"])
def delete(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    if not current_user or (current_user.id != post.author_id and current_user.role != "admin"):
        flash("Permission denied.", "danger")
        return redirect(url_for("posts.detail", slug=slug))
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("main.index"))


@posts_bp.route("/<slug>/like", methods=["POST"])
def toggle_like(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    if not current_user:
        return {"error": "Login required"}, 401
    existing = Like.query.filter_by(user_id=current_user.id, target_type="post", target_id=post.id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, target_type="post", target_id=post.id))
        liked = True
    db.session.commit()
    return {"liked": liked, "count": post.like_count}


@posts_bp.route("/<slug>/bookmark", methods=["POST"])
def toggle_bookmark(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    current_user = get_current_user()
    if not current_user:
        return {"error": "Login required"}, 401
    existing = Bookmark.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if existing:
        db.session.delete(existing)
        bookmarked = False
    else:
        db.session.add(Bookmark(user_id=current_user.id, post_id=post.id))
        bookmarked = True
    db.session.commit()
    return {"bookmarked": bookmarked}
