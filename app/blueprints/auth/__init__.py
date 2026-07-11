from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from ...extensions import db, bcrypt
from ...models.user import User
from ...utils.email import send_verification_email, send_password_reset_email

auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        display_name = request.form.get("display_name", "").strip()

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(url_for("auth.register"))

        user = User(username=username, email=email, display_name=display_name or username)
        user.set_password(password)
        user.role = "author"
        db.session.add(user)
        db.session.commit()

        send_verification_email(user)
        flash("Account created! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = (
            User.query.filter_by(email=identifier).first()
            or User.query.filter_by(username=identifier).first()
        )

        if not user or not user.check_password(password):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))
        if not user.is_active:
            flash("Your account has been suspended.", "danger")
            return redirect(url_for("auth.login"))

        session.permanent = remember
        session["user_id"] = user.id
        session["user_role"] = user.role

        from datetime import datetime
        user.last_seen = datetime.utcnow()
        db.session.commit()

        flash(f"Welcome back, {user.display_name or user.username}!", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/verify/<token>")
def verify_email(token):
    user = User.verify_token(token, salt="email-confirm")
    if not user:
        flash("Verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.login"))
    user.is_email_verified = True
    db.session.commit()
    flash("Email verified! You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(user)
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.verify_token(token, salt="password-reset")
    if not user:
        flash("Reset link is invalid or expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect(request.url)
        user.set_password(password)
        db.session.commit()
        flash("Password updated! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
