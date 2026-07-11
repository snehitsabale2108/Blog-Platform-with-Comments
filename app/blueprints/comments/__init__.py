from flask import Blueprint, request, redirect, url_for, flash, session, jsonify
from ...extensions import db
from ...models import Comment, Post, Like

comments_bp = Blueprint("comments", __name__)


def get_current_user():
    from ...models.user import User
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@comments_bp.route("/post/<int:post_id>", methods=["POST"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    current_user = get_current_user()
    if not current_user:
        flash("Please log in to comment.", "warning")
        return redirect(url_for("auth.login"))

    content = request.form.get("content", "").strip()
    parent_id = request.form.get("parent_id", type=int)

    if not content or len(content) < 2:
        flash("Comment cannot be empty.", "danger")
        return redirect(url_for("posts.detail", slug=post.slug))

    comment = Comment(
        content=content,
        post_id=post_id,
        author_id=current_user.id,
        parent_id=parent_id,
    )
    db.session.add(comment)
    db.session.commit()
    flash("Comment added!", "success")
    return redirect(url_for("posts.detail", slug=post.slug) + "#comments")


@comments_bp.route("/<int:comment_id>/edit", methods=["POST"])
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    current_user = get_current_user()
    if not current_user or current_user.id != comment.author_id:
        return jsonify({"error": "Forbidden"}), 403

    content = request.form.get("content", "").strip()
    if content:
        comment.content = content
        db.session.commit()
    post = Post.query.get(comment.post_id)
    return redirect(url_for("posts.detail", slug=post.slug) + "#comments")


@comments_bp.route("/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Forbidden"}), 403
    if current_user.id != comment.author_id and current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403
    post = Post.query.get(comment.post_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "info")
    return redirect(url_for("posts.detail", slug=post.slug) + "#comments")


@comments_bp.route("/<int:comment_id>/like", methods=["POST"])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Login required"}), 401
    existing = Like.query.filter_by(user_id=current_user.id, target_type="comment", target_id=comment_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(Like(user_id=current_user.id, target_type="comment", target_id=comment_id))
        liked = True
    db.session.commit()
    return jsonify({"liked": liked, "count": comment.like_count})
