from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ...extensions import db
from ...models.user import User
from ...models import Post, Comment, Category, Tag
from ...models.like import Like

admin_bp = Blueprint("admin", __name__, template_folder="../../templates/admin")


def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


def admin_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user = get_current_user()
        if not current_user or current_user.role != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route("/")
@admin_required
def dashboard():
    from datetime import datetime, timedelta
    current_user = get_current_user()
    stats = {
        "total_users": User.query.count(),
        "total_posts": Post.query.filter_by(status="published").count(),
        "total_comments": Comment.query.count(),
        "total_likes": Like.query.count(),
        "draft_posts": Post.query.filter_by(status="draft").count(),
        "flagged_posts": Post.query.filter_by(status="flagged").count(),
        "flagged_comments": Comment.query.filter_by(is_flagged=True).count(),
    }

    # Trending posts this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    trending = Post.query.filter(
        Post.status == "published",
        Post.published_at >= week_ago
    ).order_by(Post.view_count.desc()).limit(5).all()

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    flagged_posts = Post.query.filter_by(status="flagged").limit(5).all()
    flagged_comments = Comment.query.filter_by(is_flagged=True).limit(5).all()

    return render_template("admin/dashboard.html",
                           current_user=current_user,
                           stats=stats,
                           trending=trending,
                           recent_users=recent_users,
                           recent_comments=recent_comments,
                           flagged_posts=flagged_posts,
                           flagged_comments=flagged_comments)


@admin_bp.route("/users")
@admin_required
def manage_users():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "")
    query = User.query
    if q:
        query = query.filter(User.username.ilike(f"%{q}%") | User.email.ilike(f"%{q}%"))
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/users.html", users=users, current_user=current_user, q=q)


@admin_bp.route("/users/<int:user_id>/toggle-block", methods=["POST"])
@admin_required
def toggle_block_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user = get_current_user()
    if user.id == current_user.id:
        flash("Cannot block yourself.", "warning")
        return redirect(url_for("admin.manage_users"))
    user.is_active = not user.is_active
    db.session.commit()
    action = "unblocked" if user.is_active else "blocked"
    flash(f"User {user.username} has been {action}.", "info")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role", "author")
    if new_role in ("user", "author", "admin"):
        user.role = new_role
        db.session.commit()
        flash(f"User {user.username} role set to {new_role}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/posts")
@admin_required
def manage_posts():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)
    status = request.args.get("status", "")
    query = Post.query
    if status:
        query = query.filter_by(status=status)
    posts = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/posts.html", posts=posts, current_user=current_user, status_filter=status)


@admin_bp.route("/posts/<int:post_id>/approve", methods=["POST"])
@admin_required
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = "published"
    db.session.commit()
    flash("Post approved.", "success")
    return redirect(url_for("admin.manage_posts"))


@admin_bp.route("/posts/<int:post_id>/flag", methods=["POST"])
@admin_required
def flag_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.status = "flagged"
    db.session.commit()
    flash("Post flagged.", "warning")
    return redirect(url_for("admin.manage_posts"))


@admin_bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("admin.manage_posts"))


@admin_bp.route("/comments")
@admin_required
def manage_comments():
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)
    flagged_only = request.args.get("flagged", "0") == "1"
    query = Comment.query
    if flagged_only:
        query = query.filter_by(is_flagged=True)
    comments = query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=30, error_out=False)
    return render_template("admin/comments.html", comments=comments, current_user=current_user, flagged_only=flagged_only)


@admin_bp.route("/comments/<int:comment_id>/approve", methods=["POST"])
@admin_required
def approve_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_flagged = False
    comment.is_approved = True
    db.session.commit()
    flash("Comment approved.", "success")
    return redirect(url_for("admin.manage_comments"))


@admin_bp.route("/comments/<int:comment_id>/delete", methods=["POST"])
@admin_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "info")
    return redirect(url_for("admin.manage_comments"))


@admin_bp.route("/categories", methods=["GET", "POST"])
@admin_required
def manage_categories():
    current_user = get_current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        color = request.form.get("color", "#3b82d4")
        icon = request.form.get("icon", "bi-journal")
        if name:
            from slugify import slugify
            cat = Category(name=name, slug=slugify(name), description=description, color=color, icon=icon)
            db.session.add(cat)
            db.session.commit()
            flash("Category created.", "success")
        return redirect(url_for("admin.manage_categories"))

    categories = Category.query.all()
    return render_template("admin/categories.html", categories=categories, current_user=current_user)


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.manage_categories"))


@admin_bp.route("/tags", methods=["GET", "POST"])
@admin_required
def manage_tags():
    current_user = get_current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            from slugify import slugify
            t = Tag(name=name, slug=slugify(name))
            db.session.add(t)
            db.session.commit()
            flash("Tag created.", "success")
        return redirect(url_for("admin.manage_tags"))

    tags = Tag.query.all()
    return render_template("admin/tags.html", tags=tags, current_user=current_user)


@admin_bp.route("/tags/<int:tag_id>/delete", methods=["POST"])
@admin_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    flash("Tag deleted.", "info")
    return redirect(url_for("admin.manage_tags"))
