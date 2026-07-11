from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ...extensions import db
from ...models.user import User
from ...models import Post, Bookmark

users_bp = Blueprint("users", __name__, template_folder="../../templates/users")


def get_current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@users_bp.route("/<username>")
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    current_user = get_current_user()
    page = request.args.get("page", 1, type=int)
    posts = user.posts.filter_by(status="published").order_by(Post.published_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    is_following = current_user.is_following(user) if current_user and current_user.id != user.id else False
    return render_template("users/profile.html", profile_user=user, posts=posts,
                           is_following=is_following, current_user=current_user)


@users_bp.route("/<username>/follow", methods=["POST"])
def follow(username):
    current_user = get_current_user()
    if not current_user:
        flash("Please log in.", "warning")
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.id == user.id:
        flash("You cannot follow yourself.", "warning")
        return redirect(url_for("users.profile", username=username))
    if current_user.is_following(user):
        current_user.unfollow(user)
        flash(f"Unfollowed {user.display_name or user.username}.", "info")
    else:
        current_user.follow(user)
        flash(f"Now following {user.display_name or user.username}.", "success")
    db.session.commit()
    return redirect(url_for("users.profile", username=username))


@users_bp.route("/settings/profile", methods=["GET", "POST"])
def edit_profile():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        current_user.display_name = request.form.get("display_name", "").strip()
        current_user.bio = request.form.get("bio", "").strip()
        current_user.website = request.form.get("website", "").strip()
        current_user.twitter = request.form.get("twitter", "").strip()
        current_user.github = request.form.get("github", "").strip()
        current_user.linkedin = request.form.get("linkedin", "").strip()

        avatar = request.files.get("avatar")
        if avatar and avatar.filename:
            from ...utils.image_handler import save_image
            saved = save_image(avatar, "avatars", (300, 300))
            if saved:
                current_user.avatar_url = saved

        db.session.commit()
        flash("Profile updated!", "success")
        return redirect(url_for("users.profile", username=current_user.username))

    return render_template("users/edit_profile.html", current_user=current_user)


@users_bp.route("/settings/bookmarks")
def bookmarks():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))
    page = request.args.get("page", 1, type=int)
    saved = Bookmark.query.filter_by(user_id=current_user.id)\
        .order_by(Bookmark.created_at.desc())\
        .paginate(page=page, per_page=12, error_out=False)
    return render_template("users/bookmarks.html", bookmarks=saved, current_user=current_user)


@users_bp.route("/feed")
def feed():
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("auth.login"))
    page = request.args.get("page", 1, type=int)
    followed_ids = [u.id for u in current_user.followed.all()]
    posts = Post.query.filter(
        Post.author_id.in_(followed_ids),
        Post.status == "published"
    ).order_by(Post.published_at.desc()).paginate(page=page, per_page=12, error_out=False)
    return render_template("users/feed.html", posts=posts, current_user=current_user)
